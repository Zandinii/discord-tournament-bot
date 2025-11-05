import asyncio
from datetime import datetime, timedelta
from database.database import async_session
from database.models import Tournament, TournamentParticipant, Match, TournamentStatus, MatchStatus
from sqlalchemy import select, and_
import logging
import discord

logger = logging.getLogger('TournamentBot.Scheduler')

class NotificationScheduler:
    def __init__(self, bot):
        self.bot = bot
        self.running = False
    
    async def start(self):
        """Starta notification scheduler"""
        self.running = True
        logger.info('Notification scheduler startad')
        await self.check_notifications()
    
    async def stop(self):
        """Stoppa notification scheduler"""
        self.running = False
        logger.info('Notification scheduler stoppad')
    
    async def check_notifications(self):
        """Huvudloop som kollar notifikationer varje minut"""
        while self.running:
            try:
                await self.check_tournament_reminders()
                await self.check_match_reminders()
            except Exception as e:
                logger.error(f'Fel i notification scheduler: {e}', exc_info=True)
            
            # Vänta 1 minut innan nästa check
            await asyncio.sleep(60)
    
    async def check_tournament_reminders(self):
        """Kolla om några turneringar ska påminnas om"""
        async with async_session() as session:
            try:
                now = datetime.utcnow()
                
                # Hitta turneringar som startar inom 24 timmar
                reminder_time_24h = now + timedelta(hours=24)
                reminder_time_1h = now + timedelta(hours=1)
                
                result = await session.execute(
                    select(Tournament).where(
                        Tournament.status == TournamentStatus.SIGNUP,
                        Tournament.start_time <= reminder_time_24h,
                        Tournament.start_time > now
                    )
                )
                tournaments = result.scalars().all()
                
                for tournament in tournaments:
                    time_until = tournament.start_time - now
                    
                    # 24h reminder
                    if timedelta(hours=23, minutes=50) <= time_until <= timedelta(hours=24, minutes=10):
                        await self.send_tournament_reminder(tournament, "24 timmar")
                    
                    # 1h reminder
                    elif timedelta(minutes=50) <= time_until <= timedelta(hours=1, minutes=10):
                        await self.send_tournament_reminder(tournament, "1 timme")
                    
                    # 5 min reminder
                    elif timedelta(minutes=0) <= time_until <= timedelta(minutes=10):
                        await self.send_tournament_reminder(tournament, "5 minuter")
                
            except Exception as e:
                logger.error(f'Fel vid check av turnering reminders: {e}', exc_info=True)
    
    async def send_tournament_reminder(self, tournament, time_text: str):
        """Skicka påminnelse om turnering"""
        try:
            guild = self.bot.get_guild(tournament.guild_id)
            if not guild:
                return
            
            # Hitta kanal (använd announcement channel om det finns)
            channel = None
            if tournament.announcement_message_id:
                # Försök hitta i alla text channels
                for ch in guild.text_channels:
                    try:
                        msg = await ch.fetch_message(tournament.announcement_message_id)
                        channel = ch
                        break
                    except:
                        continue
            
            if not channel:
                # Fallback till första text channel
                channel = guild.text_channels[0] if guild.text_channels else None
            
            if not channel:
                return
            
            # Hämta deltagare
            async with async_session() as session:
                result = await session.execute(
                    select(TournamentParticipant).where(
                        TournamentParticipant.tournament_id == tournament.id
                    )
                )
                participants = result.scalars().all()
            
            # Skapa mention string för alla deltagare
            mentions = " ".join([f"<@{p.participant_id}>" for p in participants[:50]])  # Max 50 för att inte spamma
            
            embed = discord.Embed(
                title=f"⏰ Påminnelse: {tournament.name}",
                description=f"Turneringen startar om **{time_text}**!",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="📅 Starttid",
                value=f"<t:{int(tournament.start_time.timestamp())}:F>",
                inline=False
            )
            
            embed.add_field(
                name="👥 Deltagare",
                value=f"{len(participants)}/{tournament.max_participants}",
                inline=True
            )
            
            embed.add_field(
                name="🎮 Mode",
                value=tournament.game_mode,
                inline=True
            )
            
            if len(participants) < 2:
                embed.add_field(
                    name="⚠️ OBS",
                    value="Minst 2 deltagare krävs för att starta turneringen!",
                    inline=False
                )
            
            await channel.send(content=mentions if mentions else None, embed=embed)
            logger.info(f'Skickade {time_text} påminnelse för turnering {tournament.id}')
            
        except Exception as e:
            logger.error(f'Fel vid skickande av turnering reminder: {e}', exc_info=True)
    
    async def check_match_reminders(self):
        """Kolla om några matcher ska påminnas om (om de har started_at satt)"""
        async with async_session() as session:
            try:
                now = datetime.utcnow()
                reminder_time = now + timedelta(minutes=15)
                
                # Hitta matcher som ska starta snart
                result = await session.execute(
                    select(Match).where(
                        Match.status == MatchStatus.PENDING,
                        Match.started_at.isnot(None),
                        Match.started_at <= reminder_time,
                        Match.started_at > now
                    )
                )
                matches = result.scalars().all()
                
                for match in matches:
                    time_until = match.started_at - now
                    
                    # 15 min reminder
                    if timedelta(minutes=10) <= time_until <= timedelta(minutes=20):
                        await self.send_match_reminder(match)
                
            except Exception as e:
                logger.error(f'Fel vid check av match reminders: {e}', exc_info=True)
    
    async def send_match_reminder(self, match):
        """Skicka påminnelse om match"""
        try:
            async with async_session() as session:
                tournament = await session.get(Tournament, match.tournament_id)
                if not tournament:
                    return
                
                guild = self.bot.get_guild(tournament.guild_id)
                if not guild:
                    return
                
                # Hitta kanal
                channel = guild.text_channels[0] if guild.text_channels else None
                if not channel:
                    return
                
                embed = discord.Embed(
                    title=f"⏰ Match Påminnelse",
                    description=f"**Match {match.match_number}** i {tournament.name} startar snart!",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="🎮 Deltagare",
                    value=f"<@{match.participant1_id}> vs <@{match.participant2_id}>",
                    inline=False
                )
                
                if match.started_at:
                    embed.add_field(
                        name="⏰ Starttid",
                        value=f"<t:{int(match.started_at.timestamp())}:R>",
                        inline=False
                    )
                
                embed.set_footer(text=f"Match ID: {match.id}")
                
                await channel.send(
                    content=f"<@{match.participant1_id}> <@{match.participant2_id}>",
                    embed=embed
                )
                
                logger.info(f'Skickade match reminder för match {match.id}')
                
        except Exception as e:
            logger.error(f'Fel vid skickande av match reminder: {e}', exc_info=True)

# Global scheduler instance
scheduler = None

async def start_scheduler(bot):
    """Starta scheduler"""
    global scheduler
    if scheduler is None:
        scheduler = NotificationScheduler(bot)
        asyncio.create_task(scheduler.start())

async def stop_scheduler():
    """Stoppa scheduler"""
    global scheduler
    if scheduler:
        await scheduler.stop()
        scheduler = None