import discord
from discord import app_commands
from discord.ext import commands
from typing import Literal, Optional
from datetime import datetime, timedelta
from database.database import async_session
from database.models import TournamentTemplate
from utils.embeds import create_error_embed, create_success_embed
from sqlalchemy import select
import logging

logger = logging.getLogger('TournamentBot.Templates')

class TemplatesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="template-create", description="[ADMIN] Skapa en turnerings-template")
    @app_commands.describe(
        name="Template namn",
        game_mode="Spelläge",
        tournament_type="Turneringstyp",
        recurring="Ska turneringen återkomma automatiskt?",
        day_of_week="Vilken dag i veckan? (0=Måndag, 6=Söndag)",
        time="Tid på dagen (HH:MM format, t.ex. 18:00)",
        recurrence="Hur ofta ska den återkomma?"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def template_create(
        self,
        interaction: discord.Interaction,
        name: str,
        game_mode: Literal['1v1', '2v2', '5v5'],
        tournament_type: Literal['single_elim', 'double_elim', 'round_robin'],
        recurring: bool = True,
        day_of_week: Optional[int] = None,
        time: Optional[str] = None,
        recurrence: Optional[Literal['weekly', 'biweekly', 'monthly']] = 'weekly'
    ):
        """Skapa en turnerings-template"""
        
        if recurring and (day_of_week is None or time is None):
            await interaction.response.send_message(
                embed=create_error_embed('För återkommande turneringar måste du ange dag och tid!'),
                ephemeral=True
            )
            return
        
        if day_of_week is not None and (day_of_week < 0 or day_of_week > 6):
            await interaction.response.send_message(
                embed=create_error_embed('Dag måste vara mellan 0 (Måndag) och 6 (Söndag)!'),
                ephemeral=True
            )
            return
        
        # Validera tid format
        if time:
            try:
                hour, minute = map(int, time.split(':'))
                if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                    raise ValueError
            except:
                await interaction.response.send_message(
                    embed=create_error_embed('Ogiltigt tidformat! Använd HH:MM (t.ex. 18:00)'),
                    ephemeral=True
                )
                return
        
        # Öppna modal för ytterligare detaljer
        modal = TemplateModal(
            name, game_mode, tournament_type, recurring, 
            day_of_week, time, recurrence
        )
        await interaction.response.send_modal(modal)

class TemplateModal(discord.ui.Modal, title='Template Detaljer'):
    prize = discord.ui.TextInput(
        label='Pris',
        placeholder='Champion roll + skin',
        required=False,
        max_length=200
    )
    
    description = discord.ui.TextInput(
        label='Beskrivning',
        style=discord.TextStyle.paragraph,
        placeholder='Beskrivning av turneringen...',
        required=False,
        max_length=500
    )
    
    max_players = discord.ui.TextInput(
        label='Max deltagare',
        placeholder='32',
        required=False,
        default='32',
        max_length=3
    )
    
    game_name = discord.ui.TextInput(
        label='Spel (t.ex. CS2)',
        placeholder='CS2',
        required=False,
        max_length=50
    )
    
    map_pool = discord.ui.TextInput(
        label='Kartor (separera med komma)',
        style=discord.TextStyle.paragraph,
        placeholder='Dust2, Mirage, Inferno',
        required=False,
        max_length=500
    )
    
    def __init__(self, name, game_mode, tournament_type, recurring, day_of_week, time, recurrence):
        super().__init__()
        self.template_name = name
        self.game_mode = game_mode
        self.tournament_type = tournament_type
        self.recurring = recurring
        self.day_of_week = day_of_week
        self.time = time
        self.recurrence = recurrence
    
    async def on_submit(self, interaction: discord.Interaction):
        async with async_session() as session:
            try:
                max_participants = int(self.max_players.value) if self.max_players.value else 32
                
                template = TournamentTemplate(
                    guild_id=interaction.guild_id,
                    name=self.template_name,
                    game_mode=self.game_mode,
                    game_type=self.tournament_type,
                    max_participants=max_participants,
                    prize_description=self.prize.value if self.prize.value else None,
                    description=self.description.value if self.description.value else None,
                    game_name=self.game_name.value if self.game_name.value else None,
                    map_pool=self.map_pool.value if self.map_pool.value else None,
                    recurring=self.recurring,
                    recurrence_type=self.recurrence if self.recurring else None,
                    day_of_week=self.day_of_week,
                    time_of_day=self.time,
                    created_by=interaction.user.id
                )
                
                session.add(template)
                await session.commit()
                await session.refresh(template)
                
                day_names = ['Måndag', 'Tisdag', 'Onsdag', 'Torsdag', 'Fredag', 'Lördag', 'Söndag']
                recurrence_names = {
                    'weekly': 'Varje vecka',
                    'biweekly': 'Varannan vecka',
                    'monthly': 'Varje månad'
                }
                
                embed = discord.Embed(
                    title="✅ Template Skapad!",
                    description=f"**{self.template_name}** har skapats!",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="📋 Detaljer",
                    value=f"**Mode:** {self.game_mode}\n"
                          f"**Type:** {self.tournament_type}\n"
                          f"**Max deltagare:** {max_participants}",
                    inline=False
                )
                
                if self.recurring:
                    embed.add_field(
                        name="🔄 Schema",
                        value=f"**Dag:** {day_names[self.day_of_week]}\n"
                              f"**Tid:** {self.time}\n"
                              f"**Återkommer:** {recurrence_names.get(self.recurrence, self.recurrence)}",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="ℹ️ Info",
                        value="Turneringar skapas automatiskt enligt schemat!",
                        inline=False
                    )
                
                embed.set_footer(text=f"Template ID: {template.id}")
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
                logger.info(f'Template {self.template_name} skapad av {interaction.user.name}')
                
            except Exception as e:
                logger.error(f'Fel vid skapande av template: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte skapa template: {str(e)}'),
                    ephemeral=True
                )

class TemplatesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="template-list", description="[ADMIN] Lista alla templates")
    @app_commands.checks.has_permissions(administrator=True)
    async def template_list(self, interaction: discord.Interaction):
        """Lista templates"""
        
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(TournamentTemplate).where(
                        TournamentTemplate.guild_id == interaction.guild_id
                    ).order_by(TournamentTemplate.created_at.desc())
                )
                templates = result.scalars().all()
                
                if not templates:
                    await interaction.response.send_message(
                        embed=create_error_embed('Inga templates hittades!'),
                        ephemeral=True
                    )
                    return
                
                embed = discord.Embed(
                    title="📋 Turnerings Templates",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                
                day_names = ['Mån', 'Tis', 'Ons', 'Tor', 'Fre', 'Lör', 'Sön']
                
                for template in templates[:10]:
                    status = "🔄 Aktiv" if template.is_active else "⏸️ Pausad"
                    
                    info = f"**Mode:** {template.game_mode} | **Type:** {template.game_type}\n"
                    
                    if template.recurring:
                        day = day_names[template.day_of_week] if template.day_of_week is not None else '?'
                        info += f"**Schema:** {day} kl {template.time} ({template.recurrence_type})\n"
                    else:
                        info += "**Schema:** Engångsmall\n"
                    
                    if template.last_created:
                        info += f"**Senast skapad:** <t:{int(template.last_created.timestamp())}:R>"
                    
                    embed.add_field(
                        name=f"{status} - {template.name} (ID: {template.id})",
                        value=info,
                        inline=False
                    )
                
                embed.set_footer(text=f"Totalt {len(templates)} templates")
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            except Exception as e:
                logger.error(f'Fel vid listning av templates: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte lista templates: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="template-toggle", description="[ADMIN] Aktivera/pausera en template")
    @app_commands.describe(template_id="Template ID")
    @app_commands.checks.has_permissions(administrator=True)
    async def template_toggle(self, interaction: discord.Interaction, template_id: int):
        """Toggle template aktiv status"""
        
        async with async_session() as session:
            try:
                template = await session.get(TournamentTemplate, template_id)
                
                if not template:
                    await interaction.response.send_message(
                        embed=create_error_embed('Template hittades inte!'),
                        ephemeral=True
                    )
                    return
                
                if template.guild_id != interaction.guild_id:
                    await interaction.response.send_message(
                        embed=create_error_embed('Denna template tillhör inte denna server!'),
                        ephemeral=True
                    )
                    return
                
                template.is_active = not template.is_active
                await session.commit()
                
                status = "aktiverad" if template.is_active else "pausad"
                
                await interaction.response.send_message(
                    embed=create_success_embed(f'Template **{template.name}** har {status}!'),
                    ephemeral=True
                )
                
                logger.info(f'Template {template_id} {status} av {interaction.user.name}')
                
            except Exception as e:
                logger.error(f'Fel vid toggle av template: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte toggle template: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="template-delete", description="[ADMIN] Ta bort en template")
    @app_commands.describe(template_id="Template ID")
    @app_commands.checks.has_permissions(administrator=True)
    async def template_delete(self, interaction: discord.Interaction, template_id: int):
        """Ta bort template"""
        
        async with async_session() as session:
            try:
                template = await session.get(TournamentTemplate, template_id)
                
                if not template:
                    await interaction.response.send_message(
                        embed=create_error_embed('Template hittades inte!'),
                        ephemeral=True
                    )
                    return
                
                if template.guild_id != interaction.guild_id:
                    await interaction.response.send_message(
                        embed=create_error_embed('Denna template tillhör inte denna server!'),
                        ephemeral=True
                    )
                    return
                
                template_name = template.name
                await session.delete(template)
                await session.commit()
                
                await interaction.response.send_message(
                    embed=create_success_embed(f'Template **{template_name}** har tagits bort!'),
                    ephemeral=True
                )
                
                logger.info(f'Template {template_id} borttagen av {interaction.user.name}')
                
            except Exception as e:
                logger.error(f'Fel vid borttagning av template: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte ta bort template: {str(e)}'),
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(TemplatesCog(bot))