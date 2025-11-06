import asyncio
from datetime import datetime, timedelta
from database.database import async_session
from database.models import TournamentTemplate, Tournament, TournamentStatus
from sqlalchemy import select
import logging

logger = logging.getLogger('TournamentBot.TournamentScheduler')

class TournamentScheduler:
    def __init__(self, bot):
        self.bot = bot
        self.running = False
    
    async def start(self):
        """Starta tournament scheduler"""
        self.running = True
        logger.info('Tournament scheduler startad')
        await self.check_scheduled_tournaments()
    
    async def stop(self):
        """Stoppa tournament scheduler"""
        self.running = False
        logger.info('Tournament scheduler stoppad')
    
    async def check_scheduled_tournaments(self):
        """Huvudloop som kollar scheduled tournaments varje timme"""
        while self.running:
            try:
                await self.process_templates()
            except Exception as e:
                logger.error(f'Fel i tournament scheduler: {e}', exc_info=True)
            
            # Vänta 1 timme innan nästa check
            await asyncio.sleep(3600)
    
    async def process_templates(self):
        """Processa alla aktiva templates"""
        async with async_session() as session:
            try:
                now = datetime.utcnow()
                current_day = now.weekday()  # 0=Monday, 6=Sunday
                current_time = now.strftime('%H:%M')
                
                # Hämta alla aktiva recurring templates
                result = await session.execute(
                    select(TournamentTemplate).where(
                        TournamentTemplate.recurring == True,
                        TournamentTemplate.is_active == True
                    )
                )
                templates = result.scalars().all()
                
                for template in templates:
                    # Kolla om vi ska skapa turnering
                    should_create = await self.should_create_tournament(template, now, current_day, current_time)
                    
                    if should_create:
                        await self.create_tournament_from_template(template, session)
                
            except Exception as e:
                logger.error(f'Fel vid processning av templates: {e}', exc_info=True)
    
    async def should_create_tournament(self, template, now: datetime, current_day: int, current_time: str) -> bool:
        """Bestäm om en turnering ska skapas baserat på template"""
        
        # Kolla dag
        if template.day_of_week != current_day:
            return False
        
        # Kolla tid (inom 1 timme av scheduled tid)
        template_hour = int(template.time_of_day.split(':')[0])
        current_hour = now.hour
        
        if abs(template_hour - current_hour) > 1:
            return False
        
        # Kolla om vi redan skapat en turnering nyligen
        if template.last_created:
            time_since_last = now - template.last_created
            
            if template.recurrence_type == 'weekly':
                if time_since_last < timedelta(days=6):
                    return False
            elif template.recurrence_type == 'biweekly':
                if time_since_last < timedelta(days=13):
                    return False
            elif template.recurrence_type == 'monthly':
                if time_since_last < timedelta(days=28):
                    return False
        
        return True
    
    async def create_tournament_from_template(self, template, session):
        """Skapa en turnering från en template"""
        try:
            # Beräkna start time (nästa specificerade tid)
            now = datetime.utcnow()
            days_until = (template.day_of_week - now.weekday()) % 7
            if days_until == 0:
                days_until = 7  # Nästa vecka
            
            start_date = now + timedelta(days=days_until)
            hour, minute = map(int, template.time_of_day.split(':'))
            start_time = start_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Skapa turnering
            tournament = Tournament(
                guild_id=template.guild_id,
                name=template.name,
                game_mode=template.game_mode,
                game_type=template.game_type,
                max_participants=template.max_participants,
                start_time=start_time,
                prize_description=template.prize_description,
                description=template.description,
                created_by=template.created_by,
                status=TournamentStatus.SIGNUP,
                game_name=template.game_name,
                bo_format_groupstage=template.bo_format_groupstage,
                bo_format_playoffs=template.bo_format_playoffs,
                map_pool=template.map_pool
            )
            
            session.add(tournament)
            template.last_created = datetime.utcnow()
            await session.commit()
            await session.refresh(tournament)
            
            # Skicka announcement i Discord
            await self.announce_tournament(tournament)
            
            logger.info(f'Auto-skapade turnering från template: {template.name} (ID: {tournament.id})')
            
        except Exception as e:
            logger.error(f'Fel vid skapande av turnering från template: {e}', exc_info=True)
    
    async def announce_tournament(self, tournament):
        """Skicka announcement för auto-skapad turnering"""
        try:
            guild = self.bot.get_guild(tournament.guild_id)
            if not guild:
                return
            
            # Hitta första text channel
            channel = guild.text_channels[0] if guild.text_channels else None
            if not channel:
                return
            
            from utils.embeds import create_tournament_announcement
            from cogs.admin import SignupView
            
            embed = create_tournament_announcement(tournament, participant_count=0)
            view = SignupView(tournament.id)
            
            message = await channel.send(
                content="@everyone 🎮 **AUTOMATISKT SKAPAD TURNERING!**",
                embed=embed,
                view=view
            )
            
            # Spara message ID
            async with async_session() as session:
                tournament_db = await session.get(Tournament, tournament.id)
                tournament_db.announcement_message_id = message.id
                await session.commit()
            
        except Exception as e:
            logger.error(f'Fel vid announcement av auto-turnering: {e}', exc_info=True)

# Global scheduler instance
tournament_scheduler = None

async def start_tournament_scheduler(bot):
    """Starta tournament scheduler"""
    global tournament_scheduler
    if tournament_scheduler is None:
        tournament_scheduler = TournamentScheduler(bot)
        asyncio.create_task(tournament_scheduler.start())

async def stop_tournament_scheduler():
    """Stoppa tournament scheduler"""
    global tournament_scheduler
    if tournament_scheduler:
        await tournament_scheduler.stop()
        tournament_scheduler = None