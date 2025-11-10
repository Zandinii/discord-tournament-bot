import discord
from discord import app_commands
from discord.ext import commands
from typing import Literal, Optional
from datetime import datetime, timedelta
from sqlalchemy import select
from database.database import async_session
from database.models import Tournament, TournamentStatus, Guild
from utils.embeds import create_tournament_announcement, create_success_embed, create_error_embed
from utils.permissions import is_admin
import logging

logger = logging.getLogger('TournamentBot.Admin')

class TournamentModal(discord.ui.Modal, title='Skapa Turnering'):
    """Modal för att samla in turnerings-detaljer"""
    
    prize = discord.ui.TextInput(
        label='Pris',
        placeholder='Champion roll + skin',
        required=True,
        max_length=200
    )
    
    description = discord.ui.TextInput(
        label='Beskrivning (Valfritt)',
        style=discord.TextStyle.paragraph,
        placeholder='Beskrivning av turneringen...',
        required=False,
        max_length=500
    )
    
    start_time = discord.ui.TextInput(
        label='Starttid (YYYY-MM-DD HH:MM)',
        placeholder='2024-12-25 18:00',
        required=True
    )

    map_pool = discord.ui.TextInput(
        label='Kartor (separera med komma)',
        style=discord.TextStyle.paragraph,
        placeholder='Dust2, Mirage, Inferno, Nuke, Overpass, Vertigo, Ancient',
        required=True,
        max_length=500
    )
    
    bo_format = discord.ui.TextInput(
        label='Best of Format Gruppspel (1 eller 3)',
        placeholder='1 för BO1, 3 för BO3',
        required=True,
        default='1',
        max_length=1
    )
    
    def __init__(self, name: str, game_mode: str, tournament_type: Literal['single_elim', 'double_elim', 'round_robin', 'swiss'], max_players: int):
        super().__init__()
        self.tournament_name = name
        self.game_mode = game_mode
        self.tournament_type = tournament_type
        self.max_players = max_players
    
    async def on_submit(self, interaction: discord.Interaction):
        # Parse starttid
        try:
            start_time = datetime.strptime(self.start_time.value, '%Y-%m-%d %H:%M')
        except ValueError:
            await interaction.response.send_message(
                embed=create_error_embed('Ogiltigt datumformat! Använd YYYY-MM-DD HH:MM (ex: 2024-12-25 18:00)'),
                ephemeral=True
            )
            return
        
        # Kolla att tiden är i framtiden
        if start_time < datetime.now():
            await interaction.response.send_message(
                embed=create_error_embed('Starttiden måste vara i framtiden!'),
                ephemeral=True
            )
            return
        
        # Skapa turnering i databas
        async with async_session() as session:
            try:
                tournament = Tournament(
                    guild_id=interaction.guild_id,
                    name=self.tournament_name,
                    game_mode=self.game_mode,
                    game_type=self.tournament_type,
                    max_participants=self.max_players,
                    start_time=start_time,
                    prize_description=self.prize.value,
                    description=self.description.value if self.description.value else None,
                    created_by=interaction.user.id,
                    status=TournamentStatus.SIGNUP,
                    bo_format_groupstage=int(self.bo_format.value) if self.bo_format.value and self.bo_format.value.isdigit() else 1,
                    bo_format_playoffs=3,  # Always BO3 for playoffs
                    map_pool=self.map_pool.value if self.map_pool.value else None
                )
                session.add(tournament)
                await session.commit()
                await session.refresh(tournament)
                
                # Skapa announcement embed
                embed = create_tournament_announcement(tournament, participant_count=0)
                
                # Signup button
                view = SignupView(tournament.id)
                
                # Skicka announcement
                message = await interaction.channel.send(
                    content="@everyone 🎮 **NY TURNERING!**",
                    embed=embed,
                    view=view
                )
                
                # Spara message ID
                tournament.announcement_message_id = message.id
                await session.commit()
                
                await interaction.response.send_message(
                    embed=create_success_embed(f'Turnering **{self.tournament_name}** skapad! (ID: {tournament.id})'),
                    ephemeral=True
                )
                
                logger.info(f'Turnering skapad: {tournament.name} (ID: {tournament.id}) av {interaction.user.name}')
                
            except Exception as e:
                logger.error(f'Fel vid skapande av turnering: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte skapa turnering: {str(e)}'),
                    ephemeral=True
                )

class SignupView(discord.ui.View):
    """View med signup/withdraw buttons"""
    
    def __init__(self, tournament_id: int):
        super().__init__(timeout=None)
        self.tournament_id = tournament_id
    
    @discord.ui.button(label='Anmäl dig ✅', style=discord.ButtonStyle.green, custom_id='signup_button')
    async def signup_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        from database.models import TournamentParticipant, ParticipantType, Player, Team, TeamMember
        
        async with async_session() as session:
            try:
                # Hämta turnering
                tournament = await session.get(Tournament, self.tournament_id)
                
                if not tournament:
                    await interaction.response.send_message(
                        embed=create_error_embed('Turneringen hittades inte!'),
                        ephemeral=True
                    )
                    return
                
                # Kolla status
                if tournament.status != TournamentStatus.SIGNUP:
                    await interaction.response.send_message(
                        embed=create_error_embed('Anmälan är stängd för denna turnering!'),
                        ephemeral=True
                    )
                    return
                
                # KOLLA OM ANVÄNDAREN HAR SATT SIN ELO
                player = await session.get(Player, interaction.user.id)
                
                if not player or not player.elo_verified:
                    await interaction.response.send_message(
                        embed=create_error_embed(
                            '❌ Du måste sätta din ELO först!\n\n'
                            'Använd `/set-elo` för att sätta din CS2 Premier eller Faceit ELO.'
                        ),
                        ephemeral=True
                    )
                    return
                
                # KOLLA OM ANVÄNDAREN ÄR BANNAD
                from cogs.moderation import ModerationCog
                moderation_cog = interaction.client.get_cog('ModerationCog')
                if moderation_cog:
                    is_banned, ban_reason = await moderation_cog.is_user_banned(
                        interaction.user.id,
                        interaction.guild_id
                    )
                    
                    if is_banned:
                        await interaction.response.send_message(
                            embed=create_error_embed(
                                f'🚫 Du är avstängd från turneringar!\n\n'
                                f'**Anledning:** {ban_reason}'
                            ),
                            ephemeral=True
                        )
                        return
                
                # Bestäm om detta är en team-turnering (5v5 eller 2v2)
                is_team_tournament = tournament.game_mode in ['2v2', '5v5']
                
                if is_team_tournament:
                    # Team signup
                    # Hitta användarens lag
                    team_result = await session.execute(
                        select(Team).join(
                            TeamMember, Team.id == TeamMember.team_id
                        ).where(
                            TeamMember.user_id == interaction.user.id,
                            Team.guild_id == interaction.guild_id
                        )
                    )
                    team = team_result.scalar_one_or_none()
                    
                    if not team:
                        await interaction.response.send_message(
                            embed=create_error_embed('Du måste vara i ett lag för att anmäla dig till denna turnering!\n\nAnvänd `/team-create` för att skapa ett lag.'),
                            ephemeral=True
                        )
                        return
                    
                    # Kolla om användaren är captain
                    if team.captain_id != interaction.user.id:
                        await interaction.response.send_message(
                            embed=create_error_embed('Endast captain kan anmäla laget till turneringar!'),
                            ephemeral=True
                        )
                        return
                    
                    # Kolla om laget redan är anmält
                    existing = await session.execute(
                        select(TournamentParticipant).where(
                            TournamentParticipant.tournament_id == self.tournament_id,
                            TournamentParticipant.participant_id == team.id,
                            TournamentParticipant.participant_type == ParticipantType.TEAM
                        )
                    )
                    if existing.scalar_one_or_none():
                        await interaction.response.send_message(
                            embed=create_error_embed('Ditt lag är redan anmält till denna turnering!'),
                            ephemeral=True
                        )
                        return
                    
                    # Kolla max deltagare
                    participants_count = await session.execute(
                        select(TournamentParticipant).where(
                            TournamentParticipant.tournament_id == self.tournament_id
                        )
                    )
                    current_count = len(participants_count.scalars().all())
                    
                    if current_count >= tournament.max_participants:
                        await interaction.response.send_message(
                            embed=create_error_embed('Turneringen är full!'),
                            ephemeral=True
                        )
                        return
                    
                    # Anmäl lag
                    participant = TournamentParticipant(
                        tournament_id=self.tournament_id,
                        participant_id=team.id,
                        participant_type=ParticipantType.TEAM
                    )
                    session.add(participant)
                    await session.commit()
                    
                    # Uppdatera announcement embed
                    new_count = current_count + 1
                    embed = create_tournament_announcement(tournament, participant_count=new_count)
                    
                    try:
                        message = await interaction.channel.fetch_message(tournament.announcement_message_id)
                        await message.edit(embed=embed)
                    except:
                        pass
                    
                    await interaction.response.send_message(
                        embed=create_success_embed(f'✅ Lag **{team.name}** är nu anmält till **{tournament.name}**!\n\nStarttid: <t:{int(tournament.start_time.timestamp())}:F>'),
                        ephemeral=True
                    )
                    
                    logger.info(f'Lag {team.name} anmälde sig till turnering {tournament.id}')
                    
                else:
                    # Individual signup (1v1)
                    # Kolla om redan anmäld
                    existing = await session.execute(
                        select(TournamentParticipant).where(
                            TournamentParticipant.tournament_id == self.tournament_id,
                            TournamentParticipant.participant_id == interaction.user.id,
                            TournamentParticipant.participant_type == ParticipantType.USER
                        )
                    )
                    if existing.scalar_one_or_none():
                        await interaction.response.send_message(
                            embed=create_error_embed('Du är redan anmäld till denna turnering!'),
                            ephemeral=True
                        )
                        return
                    
                    # Kolla max deltagare
                    participants_count = await session.execute(
                        select(TournamentParticipant).where(
                            TournamentParticipant.tournament_id == self.tournament_id
                        )
                    )
                    current_count = len(participants_count.scalars().all())
                    
                    if current_count >= tournament.max_participants:
                        await interaction.response.send_message(
                            embed=create_error_embed('Turneringen är full!'),
                            ephemeral=True
                        )
                        return
                    
                    # Uppdatera username
                    player.username = interaction.user.name
                    
                    # Lägg till participant
                    participant = TournamentParticipant(
                        tournament_id=self.tournament_id,
                        participant_id=interaction.user.id,
                        participant_type=ParticipantType.USER
                    )
                    session.add(participant)
                    await session.commit()
                    
                    # Uppdatera announcement embed
                    new_count = current_count + 1
                    embed = create_tournament_announcement(tournament, participant_count=new_count)
                    
                    try:
                        message = await interaction.channel.fetch_message(tournament.announcement_message_id)
                        await message.edit(embed=embed)
                    except:
                        pass
                    
                    from utils.elo import get_rank_from_elo
                    rank = get_rank_from_elo(player.elo_rating)
                    
                    await interaction.response.send_message(
                        embed=create_success_embed(
                            f'✅ Du är nu anmäld till **{tournament.name}**!\n\n'
                            f'**Din ELO:** {player.elo_rating} ({rank})\n'
                            f'**Starttid:** <t:{int(tournament.start_time.timestamp())}:F>'
                        ),
                        ephemeral=True
                    )
                    
                    logger.info(f'{interaction.user.name} anmälde sig till turnering {tournament.id}')
                
            except Exception as e:
                logger.error(f'Fel vid anmälan: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte anmäla dig: {str(e)}'),
                    ephemeral=True
                )

    @discord.ui.button(label='Dra dig ur ❌', style=discord.ButtonStyle.red, custom_id='withdraw_button')
    async def withdraw_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        from database.models import TournamentParticipant, ParticipantType
        from sqlalchemy import select, delete
        
        async with async_session() as session:
            try:
                # Hämta turnering
                tournament = await session.get(Tournament, self.tournament_id)
                
                if not tournament:
                    await interaction.response.send_message(
                        embed=create_error_embed('Turneringen hittades inte!'),
                        ephemeral=True
                    )
                    return
                
                # Ta bort participant
                result = await session.execute(
                    delete(TournamentParticipant).where(
                        TournamentParticipant.tournament_id == self.tournament_id,
                        TournamentParticipant.participant_id == interaction.user.id,
                        TournamentParticipant.participant_type == ParticipantType.USER
                    )
                )
                
                if result.rowcount == 0:
                    await interaction.response.send_message(
                        embed=create_error_embed('Du är inte anmäld till denna turnering!'),
                        ephemeral=True
                    )
                    return
                
                await session.commit()
                
                # Uppdatera announcement embed
                participants = await session.execute(
                    select(TournamentParticipant).where(
                        TournamentParticipant.tournament_id == self.tournament_id
                    )
                )
                new_count = len(participants.scalars().all())
                embed = create_tournament_announcement(tournament, participant_count=new_count)
                
                try:
                    message = await interaction.channel.fetch_message(tournament.announcement_message_id)
                    await message.edit(embed=embed)
                except:
                    pass
                
                await interaction.response.send_message(
                    embed=create_success_embed(f'Du har dragit dig ur **{tournament.name}**'),
                    ephemeral=True
                )
                
                logger.info(f'{interaction.user.name} drog sig ur turnering {tournament.id}')
                
            except Exception as e:
                logger.error(f'Fel vid utträde: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte dra dig ur: {str(e)}'),
                    ephemeral=True
                )
class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="tournament-create", description="[ADMIN] Skapa en ny turnering")
    @app_commands.describe(
        name="Turneringens namn",
        game_mode="Spelläge (1v1, 2v2, 5v5)",
        tournament_type="Turneringstyp",
        max_players="Max antal deltagare"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def tournament_create(
        self,
        interaction: discord.Interaction,
        name: str,
        game_mode: Literal['1v1', '2v2', '5v5'],
        tournament_type: Literal['single_elim', 'double_elim', 'round_robin', 'swiss'],
        max_players: int = 32
    ):
        """Skapa en ny turnering med wizard"""
        
        if max_players < 2 or max_players > 128:
            await interaction.response.send_message(
                embed=create_error_embed('Max deltagare måste vara mellan 2 och 128!'),
                ephemeral=True
            )
            return
        
        # Öppna modal för ytterligare detaljer
        modal = TournamentModal(name, game_mode, tournament_type, max_players)
        await interaction.response.send_modal(modal)
    
    @app_commands.command(name="tournament-list", description="[ADMIN] Lista alla turneringar")
    @app_commands.describe(
        status="Filtrera på status"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def tournament_list(
        self,
        interaction: discord.Interaction,
        status: Optional[Literal['signup', 'ongoing', 'completed', 'cancelled']] = None
    ):
        """Lista alla turneringar"""
        from sqlalchemy import select
        
        async with async_session() as session:
            try:
                query = select(Tournament).where(Tournament.guild_id == interaction.guild_id)
                
                if status:
                    query = query.where(Tournament.status == TournamentStatus[status.upper()])
                
                query = query.order_by(Tournament.created_at.desc())
                result = await session.execute(query)
                tournaments = result.scalars().all()
                
                if not tournaments:
                    await interaction.response.send_message(
                        embed=create_error_embed('Inga turneringar hittades!'),
                        ephemeral=True
                    )
                    return
                
                embed = discord.Embed(
                    title="📋 Turneringar",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                
                for t in tournaments[:10]:  # Max 10
                    status_emoji = {
                        'signup': '✅',
                        'ongoing': '🎮',
                        'completed': '🏆',
                        'cancelled': '❌'
                    }
                    emoji = status_emoji.get(t.status.value, '❓')
                    
                    embed.add_field(
                        name=f"{emoji} {t.name} (ID: {t.id})",
                        value=f"**Mode:** {t.game_mode} | **Type:** {t.game_type}\n"
                              f"**Status:** {t.status.value.title()}\n"
                              f"**Start:** <t:{int(t.start_time.timestamp())}:R>",
                        inline=False
                    )
                
                embed.set_footer(text=f"Totalt {len(tournaments)} turneringar")
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            except Exception as e:
                logger.error(f'Fel vid listning av turneringar: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte lista turneringar: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="tournament-delete", description="[ADMIN] Ta bort en turnering")
    @app_commands.describe(tournament_id="Turnerings-ID")
    @app_commands.checks.has_permissions(administrator=True)
    async def tournament_delete(self, interaction: discord.Interaction, tournament_id: int):
        """Ta bort en turnering"""
        from sqlalchemy import delete
        
        async with async_session() as session:
            try:
                tournament = await session.get(Tournament, tournament_id)
                
                if not tournament:
                    await interaction.response.send_message(
                        embed=create_error_embed('Turneringen hittades inte!'),
                        ephemeral=True
                    )
                    return
                
                if tournament.guild_id != interaction.guild_id:
                    await interaction.response.send_message(
                        embed=create_error_embed('Denna turnering tillhör inte denna server!'),
                        ephemeral=True
                    )
                    return
                
                tournament_name = tournament.name
                await session.delete(tournament)
                await session.commit()
                
                await interaction.response.send_message(
                    embed=create_success_embed(f'Turnering **{tournament_name}** (ID: {tournament_id}) har tagits bort!'),
                    ephemeral=True
                )
                
                logger.info(f'Turnering {tournament_id} borttagen av {interaction.user.name}')
                
            except Exception as e:
                logger.error(f'Fel vid borttagning av turnering: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte ta bort turnering: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="setup", description="[ADMIN] Konfigurera bot-inställningar för servern")
    async def setup(self, interaction: discord.Interaction):
        """Initial server setup"""
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=create_error_embed('Du behöver administratörs-rättigheter!'),
                ephemeral=True
            )
            return
        
        # Skapa eller uppdatera guild i databas
        async with async_session() as session:
            try:
                guild = await session.get(Guild, interaction.guild_id)
                
                if not guild:
                    guild = Guild(guild_id=interaction.guild_id)
                    session.add(guild)
                    await session.commit()
                
                embed = discord.Embed(
                    title="⚙️ Server Setup",
                    description="Bot-inställningar har initierats!\n\n"
                                "Du kan nu använda admin-kommandon för att skapa turneringar.",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="📝 Nästa Steg",
                    value="• Använd `/tournament-create` för att skapa din första turnering\n"
                          "• Använd `/tournament-list` för att se alla turneringar",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
                logger.info(f'Server setup slutförd för guild {interaction.guild_id}')
                
            except Exception as e:
                logger.error(f'Fel vid setup: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte slutföra setup: {str(e)}'),
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(AdminCog(bot))