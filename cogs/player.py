import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime
from database.database import async_session
from database.models import (
    Tournament, TournamentParticipant, Player, 
    TournamentStatus, ParticipantType, Match
)
from utils.embeds import (
    create_player_profile, create_leaderboard, 
    create_error_embed, create_success_embed
)
from sqlalchemy import select, func, and_, or_
import logging

logger = logging.getLogger('TournamentBot.Player')

class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="signup", description="Anmäl dig till en turnering")
    @app_commands.describe(tournament_id="Turnerings-ID")
    async def signup(self, interaction: discord.Interaction, tournament_id: int):
        """Anmäl dig till en turnering"""
        async with async_session() as session:
            try:
                # Hämta turnering
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
                
                # Kolla status
                if tournament.status != TournamentStatus.SIGNUP:
                    await interaction.response.send_message(
                        embed=create_error_embed('Anmälan är stängd för denna turnering!'),
                        ephemeral=True
                    )
                    return
                
                # Kolla om redan anmäld
                existing = await session.execute(
                    select(TournamentParticipant).where(
                        TournamentParticipant.tournament_id == tournament_id,
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
                participants_result = await session.execute(
                    select(TournamentParticipant).where(
                        TournamentParticipant.tournament_id == tournament_id
                    )
                )
                current_count = len(participants_result.scalars().all())
                
                if current_count >= tournament.max_participants:
                    await interaction.response.send_message(
                        embed=create_error_embed('Turneringen är full!'),
                        ephemeral=True
                    )
                    return
                
                # Skapa/uppdatera spelarprofil
                player = await session.get(Player, interaction.user.id)
                if not player:
                    player = Player(
                        user_id=interaction.user.id,
                        guild_id=interaction.guild_id,
                        username=interaction.user.name
                    )
                    session.add(player)
                else:
                    player.username = interaction.user.name  # Uppdatera username
                
                # Lägg till participant
                participant = TournamentParticipant(
                    tournament_id=tournament_id,
                    participant_id=interaction.user.id,
                    participant_type=ParticipantType.USER
                )
                session.add(participant)
                await session.commit()
                
                await interaction.response.send_message(
                    embed=create_success_embed(
                        f'✅ Du är nu anmäld till **{tournament.name}**!\n\n'
                        f'Starttid: <t:{int(tournament.start_time.timestamp())}:F>'
                    ),
                    ephemeral=True
                )
                
                logger.info(f'{interaction.user.name} anmälde sig till turnering {tournament_id}')
                
            except Exception as e:
                logger.error(f'Fel vid anmälan: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte anmäla dig: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="withdraw", description="Dra dig ur en turnering")
    @app_commands.describe(tournament_id="Turnerings-ID")
    async def withdraw(self, interaction: discord.Interaction, tournament_id: int):
        """Dra dig ur en turnering"""
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
                
                # Ta bort participant
                result = await session.execute(
                    delete(TournamentParticipant).where(
                        TournamentParticipant.tournament_id == tournament_id,
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
                
                await interaction.response.send_message(
                    embed=create_success_embed(f'Du har dragit dig ur **{tournament.name}**'),
                    ephemeral=True
                )
                
                logger.info(f'{interaction.user.name} drog sig ur turnering {tournament_id}')
                
            except Exception as e:
                logger.error(f'Fel vid utträde: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte dra dig ur: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="my-tournaments", description="Visa dina pågående turneringar")
    async def my_tournaments(self, interaction: discord.Interaction):
        """Visa användarens pågående turneringar"""
        async with async_session() as session:
            try:
                # Hämta användarens deltaganden
                result = await session.execute(
                    select(TournamentParticipant, Tournament).join(
                        Tournament, TournamentParticipant.tournament_id == Tournament.id
                    ).where(
                        TournamentParticipant.participant_id == interaction.user.id,
                        TournamentParticipant.participant_type == ParticipantType.USER,
                        Tournament.guild_id == interaction.guild_id,
                        Tournament.status.in_([TournamentStatus.SIGNUP, TournamentStatus.ONGOING])
                    )
                )
                
                tournaments = result.all()
                
                if not tournaments:
                    await interaction.response.send_message(
                        embed=create_error_embed('Du är inte anmäld till några pågående turneringar!'),
                        ephemeral=True
                    )
                    return
                
                embed = discord.Embed(
                    title="🎮 Dina Turneringar",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                
                for participant, tournament in tournaments:
                    status_emoji = {
                        'signup': '✅ Anmälan öppen',
                        'ongoing': '🎮 Pågående',
                    }
                    
                    embed.add_field(
                        name=f"{tournament.name} (ID: {tournament.id})",
                        value=f"**Status:** {status_emoji.get(tournament.status.value, '❓')}\n"
                              f"**Mode:** {tournament.game_mode}\n"
                              f"**Start:** <t:{int(tournament.start_time.timestamp())}:R>",
                        inline=False
                    )
                
                embed.set_footer(text=f"{len(tournaments)} aktiva turneringar")
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            except Exception as e:
                logger.error(f'Fel vid hämtning av turneringar: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte hämta turneringar: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="my-stats", description="Visa din statistik")
    async def my_stats(self, interaction: discord.Interaction):
        """Visa användarens statistik"""
        async with async_session() as session:
            try:
                player = await session.get(Player, interaction.user.id)
                
                if not player:
                    # Skapa ny spelare
                    player = Player(
                        user_id=interaction.user.id,
                        guild_id=interaction.guild_id,
                        username=interaction.user.name
                    )
                    session.add(player)
                    await session.commit()
                
                # Hämta senaste matcher (kommer att implementeras senare)
                recent_matches = []
                
                embed = create_player_profile(player, recent_matches)
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            except Exception as e:
                logger.error(f'Fel vid hämtning av stats: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte hämta statistik: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="profile", description="Visa en spelares profil")
    @app_commands.describe(user="Användaren att visa profil för")
    async def profile(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        """Visa spelarprofil"""
        target_user = user or interaction.user
        
        async with async_session() as session:
            try:
                player = await session.get(Player, target_user.id)
                
                if not player:
                    await interaction.response.send_message(
                        embed=create_error_embed(f'{target_user.name} har ingen profil ännu!'),
                        ephemeral=True
                    )
                    return
                
                # Hämta senaste matcher
                recent_matches = []
                
                embed = create_player_profile(player, recent_matches)
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            except Exception as e:
                logger.error(f'Fel vid hämtning av profil: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte hämta profil: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="leaderboard", description="Visa topp-spelare")
    @app_commands.describe(category="Kategori att sortera efter")
    async def leaderboard(
        self, 
        interaction: discord.Interaction,
        category: Optional[str] = 'elo'
    ):
        """Visa leaderboard"""
        async with async_session() as session:
            try:
                query = select(Player).where(Player.guild_id == interaction.guild_id)
                
                if category == 'wins':
                    query = query.order_by(Player.total_wins.desc())
                elif category == 'tournaments':
                    query = query.order_by(Player.tournaments_won.desc())
                else:  # default elo
                    query = query.order_by(Player.elo_rating.desc())
                
                query = query.limit(10)
                
                result = await session.execute(query)
                players = result.scalars().all()
                
                if not players:
                    await interaction.response.send_message(
                        embed=create_error_embed('Inga spelare hittades!'),
                        ephemeral=True
                    )
                    return
                
                embed = create_leaderboard(list(players), category)
                
                await interaction.response.send_message(embed=embed)
                
            except Exception as e:
                logger.error(f'Fel vid hämtning av leaderboard: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte hämta leaderboard: {str(e)}'),
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(PlayerCog(bot))