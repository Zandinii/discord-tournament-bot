import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime, timedelta
from database.database import async_session
from database.models import (
    Season, SeasonStats, Player, Tournament, Match,
    MatchHistory, TournamentStatus, Guild
)
from utils.embeds import create_error_embed, create_success_embed
from sqlalchemy import select, func, and_, desc
import logging

logger = logging.getLogger('TournamentBot.Season')

class SeasonCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="season-create", description="[ADMIN] Skapa en ny säsong")
    @app_commands.describe(
        name="Säsongens namn (t.ex. 'Season 1', 'Winter 2024')",
        duration_days="Hur många dagar säsongen ska vara (standard: 90)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def season_create(
        self, 
        interaction: discord.Interaction, 
        name: str,
        duration_days: int = 90
    ):
        """Skapa en ny säsong"""
        
        async with async_session() as session:
            try:
                # Kolla om det redan finns en aktiv säsong
                existing = await session.execute(
                    select(Season).where(
                        Season.guild_id == interaction.guild_id,
                        Season.is_active == True
                    )
                )
                active_season = existing.scalar_one_or_none()
                
                if active_season:
                    await interaction.response.send_message(
                        embed=create_error_embed(
                            f'Det finns redan en aktiv säsong: **{active_season.name}**\n\n'
                            f'Använd `/season-end` för att avsluta den först.'
                        ),
                        ephemeral=True
                    )
                    return
                
                # Skapa ny säsong
                start_date = datetime.utcnow()
                end_date = start_date + timedelta(days=duration_days)
                
                season = Season(
                    guild_id=interaction.guild_id,
                    name=name,
                    start_date=start_date,
                    end_date=end_date,
                    is_active=True
                )
                session.add(season)
                await session.commit()
                await session.refresh(season)
                
                # Skapa stats för alla befintliga spelare
                players_result = await session.execute(
                    select(Player).where(Player.guild_id == interaction.guild_id)
                )
                players = players_result.scalars().all()
                
                for player in players:
                    season_stats = SeasonStats(
                        season_id=season.id,
                        user_id=player.user_id,
                        guild_id=interaction.guild_id,
                        elo_rating=player.elo_rating
                    )
                    session.add(season_stats)
                    player.current_season_id = season.id
                
                await session.commit()
                
                embed = discord.Embed(
                    title="🎊 Ny Säsong Skapad!",
                    description=f"**{name}** har startats!",
                    color=discord.Color.gold(),
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="📅 Startdatum",
                    value=f"<t:{int(start_date.timestamp())}:F>",
                    inline=True
                )
                
                embed.add_field(
                    name="📅 Slutdatum",
                    value=f"<t:{int(end_date.timestamp())}:F>",
                    inline=True
                )
                
                embed.add_field(
                    name="⏱️ Längd",
                    value=f"{duration_days} dagar",
                    inline=True
                )
                
                embed.add_field(
                    name="👥 Spelare",
                    value=f"{len(players)} spelare registrerade",
                    inline=False
                )
                
                embed.set_footer(text=f"Season ID: {season.id}")
                
                await interaction.response.send_message(
                    content="@everyone 🎉 **NY SÄSONG!**",
                    embed=embed
                )
                
                logger.info(f'Säsong {name} skapad av {interaction.user.name}')
                
            except Exception as e:
                logger.error(f'Fel vid skapande av säsong: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte skapa säsong: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="season-end", description="[ADMIN] Avsluta nuvarande säsong")
    @app_commands.checks.has_permissions(administrator=True)
    async def season_end(self, interaction: discord.Interaction):
        """Avsluta aktiv säsong"""
        
        async with async_session() as session:
            try:
                # Hitta aktiv säsong
                result = await session.execute(
                    select(Season).where(
                        Season.guild_id == interaction.guild_id,
                        Season.is_active == True
                    )
                )
                season = result.scalar_one_or_none()
                
                if not season:
                    await interaction.response.send_message(
                        embed=create_error_embed('Det finns ingen aktiv säsong!'),
                        ephemeral=True
                    )
                    return
                
                # Avsluta säsong
                season.is_active = False
                season.end_date = datetime.utcnow()
                
                # Hämta top 3 spelare
                top_players = await session.execute(
                    select(SeasonStats, Player).join(
                        Player, SeasonStats.user_id == Player.user_id
                    ).where(
                        SeasonStats.season_id == season.id,
                        SeasonStats.guild_id == interaction.guild_id
                    ).order_by(SeasonStats.elo_rating.desc()).limit(3)
                )
                top_3 = top_players.all()
                
                await session.commit()
                
                embed = discord.Embed(
                    title=f"🏁 {season.name} Avslutad!",
                    description="Tack för denna säsongen!",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                
                # Top 3
                medals = ['🥇', '🥈', '🥉']
                if top_3:
                    top_text = ""
                    for i, (stats, player) in enumerate(top_3):
                        top_text += f"{medals[i]} <@{player.user_id}> - {stats.elo_rating} ELO\n"
                    
                    embed.add_field(
                        name="🏆 Top 3 Spelare",
                        value=top_text,
                        inline=False
                    )
                
                embed.add_field(
                    name="📊 Säsongsstatistik",
                    value=f"Avslutad: <t:{int(datetime.utcnow().timestamp())}:F>",
                    inline=False
                )
                
                await interaction.response.send_message(
                    content="@everyone",
                    embed=embed
                )
                
                logger.info(f'Säsong {season.name} avslutad av {interaction.user.name}')
                
            except Exception as e:
                logger.error(f'Fel vid avslutande av säsong: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte avsluta säsong: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="season-info", description="Visa information om nuvarande säsong")
    async def season_info(self, interaction: discord.Interaction):
        """Visa säsongsinformation"""
        
        async with async_session() as session:
            try:
                # Hitta aktiv säsong
                result = await session.execute(
                    select(Season).where(
                        Season.guild_id == interaction.guild_id,
                        Season.is_active == True
                    )
                )
                season = result.scalar_one_or_none()
                
                if not season:
                    await interaction.response.send_message(
                        embed=create_error_embed('Det finns ingen aktiv säsong!'),
                        ephemeral=True
                    )
                    return
                
                # Statistik
                stats_count = await session.execute(
                    select(func.count(SeasonStats.id)).where(
                        SeasonStats.season_id == season.id
                    )
                )
                player_count = stats_count.scalar()
                
                # Turneringar i säsongen
                tournaments = await session.execute(
                    select(func.count(Tournament.id)).where(
                        Tournament.season_id == season.id
                    )
                )
                tournament_count = tournaments.scalar()
                
                # Tid kvar
                time_left = season.end_date - datetime.utcnow()
                days_left = time_left.days
                
                embed = discord.Embed(
                    title=f"📊 {season.name}",
                    description="Nuvarande säsongsinformation",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="📅 Startdatum",
                    value=f"<t:{int(season.start_date.timestamp())}:D>",
                    inline=True
                )
                
                embed.add_field(
                    name="📅 Slutdatum",
                    value=f"<t:{int(season.end_date.timestamp())}:D>",
                    inline=True
                )
                
                embed.add_field(
                    name="⏱️ Tid Kvar",
                    value=f"{days_left} dagar",
                    inline=True
                )
                
                embed.add_field(
                    name="👥 Aktiva Spelare",
                    value=str(player_count),
                    inline=True
                )
                
                embed.add_field(
                    name="🏆 Turneringar",
                    value=str(tournament_count),
                    inline=True
                )
                
                embed.set_footer(text=f"Season ID: {season.id}")
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            except Exception as e:
                logger.error(f'Fel vid hämtning av säsong info: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte hämta säsong info: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="season-leaderboard", description="Visa säsongens leaderboard")
    @app_commands.describe(
        season_name="Vilken säsong (lämna tom för nuvarande)"
    )
    async def season_leaderboard(
        self, 
        interaction: discord.Interaction,
        season_name: Optional[str] = None
    ):
        """Visa säsongens leaderboard"""
        
        async with async_session() as session:
            try:
                # Hitta säsong
                if season_name:
                    result = await session.execute(
                        select(Season).where(
                            Season.guild_id == interaction.guild_id,
                            Season.name.ilike(f'%{season_name}%')
                        )
                    )
                else:
                    result = await session.execute(
                        select(Season).where(
                            Season.guild_id == interaction.guild_id,
                            Season.is_active == True
                        )
                    )
                
                season = result.scalar_one_or_none()
                
                if not season:
                    await interaction.response.send_message(
                        embed=create_error_embed('Säsongen hittades inte!'),
                        ephemeral=True
                    )
                    return
                
                # Hämta top 10
                top_players = await session.execute(
                    select(SeasonStats, Player).join(
                        Player, SeasonStats.user_id == Player.user_id
                    ).where(
                        SeasonStats.season_id == season.id,
                        SeasonStats.guild_id == interaction.guild_id
                    ).order_by(SeasonStats.elo_rating.desc()).limit(10)
                )
                players = top_players.all()
                
                if not players:
                    await interaction.response.send_message(
                        embed=create_error_embed('Inga spelare hittades för denna säsong!'),
                        ephemeral=True
                    )
                    return
                
                embed = discord.Embed(
                    title=f"🏆 {season.name} - Leaderboard",
                    description="Top 10 spelare denna säsongen",
                    color=discord.Color.gold(),
                    timestamp=datetime.utcnow()
                )
                
                medals = ['🥇', '🥈', '🥉']
                leaderboard_text = ""
                
                for i, (stats, player) in enumerate(players, 1):
                    medal = medals[i-1] if i <= 3 else f"`#{i}`"
                    win_rate = (stats.wins / stats.matches_played * 100) if stats.matches_played > 0 else 0
                    
                    leaderboard_text += (
                        f"{medal} **{player.username}**\n"
                        f"├ ELO: {stats.elo_rating}\n"
                        f"├ Matcher: {stats.matches_played} ({stats.wins}W-{stats.losses}L)\n"
                        f"└ Win Rate: {win_rate:.1f}%\n\n"
                    )
                
                embed.description += f"\n\n{leaderboard_text}"
                
                embed.set_footer(
                    text=f"{'Aktiv säsong' if season.is_active else 'Avslutad säsong'} | Season ID: {season.id}"
                )
                
                await interaction.response.send_message(embed=embed)
                
            except Exception as e:
                logger.error(f'Fel vid hämtning av leaderboard: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte hämta leaderboard: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="season-list", description="Lista alla säsonger")
    async def season_list(self, interaction: discord.Interaction):
        """Lista alla säsonger"""
        
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(Season).where(
                        Season.guild_id == interaction.guild_id
                    ).order_by(Season.created_at.desc())
                )
                seasons = result.scalars().all()
                
                if not seasons:
                    await interaction.response.send_message(
                        embed=create_error_embed('Inga säsonger hittades!'),
                        ephemeral=True
                    )
                    return
                
                embed = discord.Embed(
                    title="📋 Alla Säsonger",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                
                for season in seasons[:10]:  # Max 10
                    status = "✅ Aktiv" if season.is_active else "🏁 Avslutad"
                    
                    embed.add_field(
                        name=f"{status} - {season.name}",
                        value=f"**Start:** <t:{int(season.start_date.timestamp())}:D>\n"
                              f"**Slut:** <t:{int(season.end_date.timestamp())}:D>\n"
                              f"**ID:** {season.id}",
                        inline=False
                    )
                
                embed.set_footer(text=f"Totalt {len(seasons)} säsonger")
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            except Exception as e:
                logger.error(f'Fel vid listning av säsonger: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte lista säsonger: {str(e)}'),
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(SeasonCog(bot))