import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Literal
from datetime import datetime
from database.database import async_session
from database.models import (
    Tournament, TournamentParticipant, Player, 
    TournamentStatus, ParticipantType, Match,
    MatchHistory
)
from utils.embeds import (
    create_player_profile, create_leaderboard, 
    create_error_embed, create_success_embed
)
from utils.elo import (
    convert_premier_to_elo, convert_faceit_to_elo,
    validate_premier_elo, validate_faceit_level, validate_faceit_elo,
    get_rank_from_elo, get_elo_tier_color
)
from sqlalchemy import select, func, and_, or_
import logging

logger = logging.getLogger('TournamentBot.Player')

class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="set-elo", description="Sätt din CS2 Premier eller Faceit ELO")
    @app_commands.describe(
        elo_type="Välj Premier eller Faceit",
        premier_elo="Din CS2 Premier ELO (0-35000)",
        faceit_level="Din Faceit Level (1-10)",
        faceit_elo="Din Faceit ELO (500-3500, valfritt för level 10)"
    )
    async def set_elo(
        self,
        interaction: discord.Interaction,
        elo_type: Literal['premier', 'faceit'],
        premier_elo: Optional[int] = None,
        faceit_level: Optional[int] = None,
        faceit_elo: Optional[int] = 1000
    ):
        """Sätt din ELO från CS2 Premier eller Faceit"""
        
        async with async_session() as session:
            try:
                # Validering
                if elo_type == 'premier':
                    if premier_elo is None:
                        await interaction.response.send_message(
                            embed=create_error_embed('Du måste ange din Premier ELO!'),
                            ephemeral=True
                        )
                        return
                    
                    if not validate_premier_elo(premier_elo):
                        await interaction.response.send_message(
                            embed=create_error_embed('Premier ELO måste vara mellan 0 och 35000!'),
                            ephemeral=True
                        )
                        return
                    
                    # Konvertera till vårt system
                    our_elo = convert_premier_to_elo(premier_elo)
                    source_text = f"CS2 Premier: {premier_elo}"
                    
                elif elo_type == 'faceit':
                    if faceit_level is None:
                        await interaction.response.send_message(
                            embed=create_error_embed('Du måste ange din Faceit Level!'),
                            ephemeral=True
                        )
                        return
                    
                    if not validate_faceit_level(faceit_level):
                        await interaction.response.send_message(
                            embed=create_error_embed('Faceit Level måste vara mellan 1 och 10!'),
                            ephemeral=True
                        )
                        return
                    
                    if faceit_elo and not validate_faceit_elo(faceit_elo):
                        await interaction.response.send_message(
                            embed=create_error_embed('Faceit ELO måste vara mellan 500 och 3500!'),
                            ephemeral=True
                        )
                        return
                    
                    # Konvertera till vårt system
                    our_elo = convert_faceit_to_elo(faceit_level, faceit_elo)
                    source_text = f"Faceit Level {faceit_level}"
                    if faceit_level == 10:
                        source_text += f" ({faceit_elo} ELO)"
                
                # Skapa eller uppdatera spelare
                player = await session.get(Player, interaction.user.id)
                
                if not player:
                    player = Player(
                        user_id=interaction.user.id,
                        guild_id=interaction.guild_id,
                        username=interaction.user.name,
                        elo_rating=our_elo,
                        highest_elo=our_elo
                    )
                    session.add(player)
                else:
                    player.username = interaction.user.name
                    player.elo_rating = our_elo
                    if our_elo > player.highest_elo:
                        player.highest_elo = our_elo
                
                # Sätt ELO source info
                player.elo_verified = True
                player.elo_source = elo_type
                
                if elo_type == 'premier':
                    player.cs2_premier_elo = premier_elo
                    player.faceit_level = None
                    player.faceit_elo = None
                else:
                    player.faceit_level = faceit_level
                    player.faceit_elo = faceit_elo if faceit_level == 10 else None
                    player.cs2_premier_elo = None
                
                await session.commit()
                
                # Skapa embed
                rank = get_rank_from_elo(our_elo)
                color = get_elo_tier_color(our_elo)
                
                embed = discord.Embed(
                    title="✅ ELO Inställd!",
                    description=f"Din ELO har uppdaterats baserat på din {source_text}",
                    color=color,
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="🎯 Din ELO",
                    value=f"**{our_elo}** ELO",
                    inline=True
                )
                
                embed.add_field(
                    name="🏆 Rank",
                    value=rank,
                    inline=True
                )
                
                embed.add_field(
                    name="📊 Källa",
                    value=source_text,
                    inline=False
                )
                
                embed.set_footer(text="Du kan nu anmäla dig till turneringar!")
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
                logger.info(f'{interaction.user.name} satte ELO till {our_elo} från {elo_type}')
                
            except Exception as e:
                logger.error(f'Fel vid setting av ELO: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte sätta ELO: {str(e)}'),
                    ephemeral=True
                )
    
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
                moderation_cog = self.bot.get_cog('ModerationCog')
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
                
                # Uppdatera username
                player.username = interaction.user.name
                
                # Lägg till participant
                participant = TournamentParticipant(
                    tournament_id=tournament_id,
                    participant_id=interaction.user.id,
                    participant_type=ParticipantType.USER
                )
                session.add(participant)
                await session.commit()
                
                rank = get_rank_from_elo(player.elo_rating)
                
                await interaction.response.send_message(
                    embed=create_success_embed(
                        f'✅ Du är nu anmäld till **{tournament.name}**!\n\n'
                        f'**Din ELO:** {player.elo_rating} ({rank})\n'
                        f'**Starttid:** <t:{int(tournament.start_time.timestamp())}:F>'
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
                    color=0x0099ff,
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
    
    @app_commands.command(name="my-stats", description="Visa din statistik för aktiv säsong")
    async def my_stats(self, interaction: discord.Interaction):
        """Visa användarens statistik för nuvarande säsong"""
        async with async_session() as session:
            try:
                # Hämta aktiv säsong
                from database.models import Season, SeasonStats
                
                active_season = await session.execute(
                    select(Season).where(
                        Season.guild_id == interaction.guild_id,
                        Season.is_active == True
                    )
                )
                season = active_season.scalar_one_or_none()
                
                if not season:
                    await interaction.response.send_message(
                        embed=create_error_embed('Det finns ingen aktiv säsong!'),
                        ephemeral=True
                    )
                    return
                
                # Hämta season stats
                season_stats = await session.execute(
                    select(SeasonStats).where(
                        SeasonStats.season_id == season.id,
                        SeasonStats.user_id == interaction.user.id
                    )
                )
                stats = season_stats.scalar_one_or_none()
                
                if not stats:
                    await interaction.response.send_message(
                        embed=create_error_embed('Du har ingen statistik för denna säsong än!'),
                        ephemeral=True
                    )
                    return
                
                win_rate = (stats.wins / stats.matches_played * 100) if stats.matches_played > 0 else 0
                rank = get_rank_from_elo(stats.elo_rating)
                color = get_elo_tier_color(stats.elo_rating)
                
                embed = discord.Embed(
                    title=f"📊 {interaction.user.name} - Säsong Stats",
                    description=f"**{season.name}**",
                    color=color,
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="🎯 ELO & Rank",
                    value=f"**{stats.elo_rating}** ELO\n{rank}",
                    inline=True
                )
                
                embed.add_field(
                    name="📈 Högsta ELO",
                    value=f"**{stats.highest_elo}**",
                    inline=True
                )
                
                embed.add_field(
                    name="🎮 Matcher",
                    value=f"**{stats.matches_played}** spelade\n"
                          f"**{stats.wins}** vinster\n"
                          f"**{stats.losses}** förluster",
                    inline=True
                )
                
                embed.add_field(
                    name="📊 Win Rate",
                    value=f"**{win_rate:.1f}%**",
                    inline=True
                )
                
                embed.add_field(
                    name="🏆 Turneringar",
                    value=f"**{stats.tournaments_played}** deltagna\n"
                          f"**{stats.tournaments_won}** vunna",
                    inline=True
                )
                
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                embed.set_footer(text=f"Säsong: {season.name}")
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            except Exception as e:
                logger.error(f'Fel vid hämtning av stats: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte hämta statistik: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="profile", description="Visa total spelarprofil (alla säsonger)")
    @app_commands.describe(user="Användaren att visa profil för")
    async def profile(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        """Visa spelarprofil med total statistik"""
        target_user = user or interaction.user
        
        async with async_session() as session:
            try:
                player = await session.get(Player, target_user.id)
                
                if not player:
                    await interaction.response.send_message(
                        embed=create_error_embed(f'{target_user.name} har ingen profil än!'),
                        ephemeral=True
                    )
                    return
                
                win_rate = (player.total_wins / player.total_matches * 100) if player.total_matches > 0 else 0
                rank = get_rank_from_elo(player.elo_rating)
                color = get_elo_tier_color(player.elo_rating)
                
                embed = discord.Embed(
                    title=f"👤 {player.username}",
                    description="**All-Time Statistik**",
                    color=color,
                    timestamp=datetime.utcnow()
                )
                
                # ELO Info
                elo_text = f"**{player.elo_rating}** ELO\n{rank}"
                if player.elo_verified:
                    source_map = {
                        'premier': f"CS2 Premier ({player.cs2_premier_elo})",
                        'faceit': f"Faceit Level {player.faceit_level}"
                    }
                    elo_text += f"\n*Källa: {source_map.get(player.elo_source, 'Okänd')}*"
                
                embed.add_field(
                    name="🎯 ELO & Rank",
                    value=elo_text,
                    inline=True
                )
                
                embed.add_field(
                    name="📈 Högsta ELO",
                    value=f"**{player.highest_elo}**",
                    inline=True
                )
                
                embed.add_field(
                    name="🎮 Totala Matcher",
                    value=f"**{player.total_matches}** spelade\n"
                          f"**{player.total_wins}** vinster\n"
                          f"**{player.total_losses}** förluster",
                    inline=True
                )
                
                embed.add_field(
                    name="📊 Win Rate",
                    value=f"**{win_rate:.1f}%**",
                    inline=True
                )
                
                embed.add_field(
                    name="🔥 Win Streak",
                    value=f"**Nuvarande:** {player.win_streak}\n"
                          f"**Bästa:** {player.best_win_streak}",
                    inline=True
                )
                
                embed.add_field(
                    name="🏆 Turneringar",
                    value=f"**{player.tournaments_participated}** deltagna\n"
                          f"**{player.tournaments_won}** vunna",
                    inline=True
                )
                
                embed.set_thumbnail(url=target_user.display_avatar.url)
                embed.set_footer(text=f"Medlem sedan {player.created_at.strftime('%Y-%m-%d')}")
                
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

    @app_commands.command(name="match-history", description="Visa din match-historik")
    @app_commands.describe(user="Användare att visa historik för (valfritt)")
    async def match_history(
        self, 
        interaction: discord.Interaction,
        user: Optional[discord.User] = None
    ):
        """Visa match-historik"""
        
        target_user = user or interaction.user
        
        async with async_session() as session:
            try:
                # Hämta senaste 10 matcher
                result = await session.execute(
                    select(MatchHistory, Player).outerjoin(
                        Player, MatchHistory.opponent_id == Player.user_id
                    ).where(
                        MatchHistory.user_id == target_user.id
                    ).order_by(MatchHistory.played_at.desc()).limit(10)
                )
                
                matches = result.all()
                
                if not matches:
                    await interaction.response.send_message(
                        embed=create_error_embed(f'{target_user.mention} har ingen match-historik!'),
                        ephemeral=True
                    )
                    return
                
                embed = discord.Embed(
                    title=f"📜 Match Historik - {target_user.name}",
                    color=0x0099ff,
                    timestamp=datetime.utcnow()
                )
                
                for history, opponent in matches:
                    result_emoji = "✅" if history.won else "❌"
                    elo_emoji = "📈" if history.elo_change > 0 else "📉"
                    opponent_name = opponent.username if opponent else f"Spelare {history.opponent_id}"
                    
                    embed.add_field(
                        name=f"{result_emoji} vs {opponent_name}",
                        value=f"{elo_emoji} {history.elo_before} → {history.elo_after} ({history.elo_change:+d})\n"
                              f"<t:{int(history.played_at.timestamp())}:R>",
                        inline=False
                    )
                
                embed.set_footer(text="Senaste 10 matcherna")
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            except Exception as e:
                logger.error(f'Fel vid hämtning av match history: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte hämta match history: {str(e)}'),
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(PlayerCog(bot))