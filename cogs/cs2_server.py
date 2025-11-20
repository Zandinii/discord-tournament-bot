"""
CS2 Server Discord Cog
Admin commands och event handlers för CS2 server automation
"""

import discord
import asyncio
import os
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime

from database.database import async_session
from database.models import (
    CS2ServerConfig, PlayerSteamID, Match, MatchStatus, MatchServerLog
)
from utils.embeds import create_error_embed, create_success_embed
from utils.permissions import is_tournament_admin
from utils.cs2_server_manager import CS2ServerManager, start_match_server, stop_match_server
from sqlalchemy import select
import logging

logger = logging.getLogger('TournamentBot.CS2Server')


class CS2ServerCog(commands.Cog):
    """Cog för CS2 server integration"""
    
    def __init__(self, bot):
        self.bot = bot
        self.server_manager = CS2ServerManager(bot)
    
    @commands.Cog.listener()
    async def on_match_created(self, match_id: int):
        """
        Event som triggas när en match skapas
        Detta är kärnan i automationen!
        """
        try:
            logger.info(f'🎮 Match {match_id} skapad - startar CS2 server automation')
            
            async with async_session() as session:
                match = await session.get(Match, match_id)
                if not match:
                    return
                
                # Kolla om CS2 automation är aktiverad
                config = await session.execute(
                    select(CS2ServerConfig).where(
                        CS2ServerConfig.guild_id == match.tournament.guild_id,
                        CS2ServerConfig.enabled == True
                    )
                )
                server_config = config.scalar_one_or_none()
                
                if not server_config:
                    logger.info(f'CS2 automation inte aktiverad för guild {match.tournament.guild_id}')
                    return
                
                # Starta server automation i bakgrunden
                asyncio.create_task(self.server_manager.setup_match_server(match_id))
        
        except Exception as e:
            logger.error(f'Fel i on_match_created: {e}', exc_info=True)
    
    @commands.Cog.listener()
    async def on_match_completed(self, match_id: int):
        """
        Event som triggas när en match är slutförd
        Stänger automatiskt ner servern
        """
        try:
            logger.info(f'✅ Match {match_id} slutförd - schemalägger server shutdown')
            
            async with async_session() as session:
                match = await session.get(Match, match_id)
                if not match:
                    return
                
                config = await session.execute(
                    select(CS2ServerConfig).where(
                        CS2ServerConfig.guild_id == match.tournament.guild_id,
                        CS2ServerConfig.enabled == True
                    )
                )
                server_config = config.scalar_one_or_none()
                
                if not server_config:
                    return
                
                # Stäng ner server efter delay
                delay = server_config.auto_shutdown_delay or 300
                asyncio.create_task(stop_match_server(self.bot, match_id, delay))
        
        except Exception as e:
            logger.error(f'Fel i on_match_completed: {e}', exc_info=True)
    
    @app_commands.command(
        name="cs2-setup",
        description="[ADMIN] Konfigurera CS2 server automation"
    )
    @app_commands.describe(
        panel_url="Pterodactyl Panel URL (ex: https://panel.example.com)",
        server_uuid="Server UUID från Pterodactyl",
        server_ip="Server IP-adress",
        server_port="Server port (default: 27015)",
        server_password="Server password (valfritt)"
    )
    @is_tournament_admin()
    async def cs2_setup(
        self,
        interaction: discord.Interaction,
        panel_url: str,
        server_uuid: str,
        server_ip: str,
        server_port: int = 27015,
        server_password: Optional[str] = None
    ):
        """Konfigurera CS2 server automation för denna guild"""
        
        async with async_session() as session:
            try:
                # Kolla om config redan finns
                result = await session.execute(
                    select(CS2ServerConfig).where(
                        CS2ServerConfig.guild_id == interaction.guild_id
                    )
                )
                config = result.scalar_one_or_none()
                
                if config:
                    # Uppdatera befintlig
                    config.ptero_panel_url = panel_url
                    config.ptero_server_uuid = server_uuid
                    config.server_ip = server_ip
                    config.server_port = server_port
                    config.server_password = server_password
                    config.enabled = True
                else:
                    # Skapa ny
                    config = CS2ServerConfig(
                        guild_id=interaction.guild_id,
                        ptero_panel_url=panel_url,
                        ptero_server_uuid=server_uuid,
                        server_ip=server_ip,
                        server_port=server_port,
                        server_password=server_password,
                        enabled=True
                    )
                    session.add(config)
                
                await session.commit()
                
                embed = discord.Embed(
                    title="✅ CS2 Server Konfigurerad!",
                    description="Automatisk server-hantering är nu aktiverad",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="📡 Server Info",
                    value=f"**IP:** {server_ip}:{server_port}\n"
                          f"**UUID:** `{server_uuid[:8]}...`",
                    inline=False
                )
                
                embed.add_field(
                    name="🔧 Panel",
                    value=f"{panel_url}",
                    inline=False
                )
                
                embed.set_footer(text="Servern startas automatiskt när matcher skapas")
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                logger.info(f'CS2 server konfigurerad för guild {interaction.guild_id}')
            
            except Exception as e:
                logger.error(f'Fel vid CS2 setup: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte konfigurera CS2 server: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(
        name="cs2-toggle",
        description="[ADMIN] Aktivera/avaktivera CS2 automation"
    )
    @app_commands.describe(enabled="Aktivera eller avaktivera automation")
    @is_tournament_admin()
    async def cs2_toggle(
        self,
        interaction: discord.Interaction,
        enabled: bool
    ):
        """Toggle CS2 server automation"""
        
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(CS2ServerConfig).where(
                        CS2ServerConfig.guild_id == interaction.guild_id
                    )
                )
                config = result.scalar_one_or_none()
                
                if not config:
                    await interaction.response.send_message(
                        embed=create_error_embed(
                            'CS2 server är inte konfigurerad! Använd `/cs2-setup` först.'
                        ),
                        ephemeral=True
                    )
                    return
                
                config.enabled = enabled
                await session.commit()
                
                status = "aktiverad" if enabled else "avaktiverad"
                emoji = "✅" if enabled else "❌"
                
                await interaction.response.send_message(
                    embed=create_success_embed(
                        f'{emoji} CS2 automation är nu **{status}**'
                    ),
                    ephemeral=True
                )
                
                logger.info(f'CS2 automation {status} för guild {interaction.guild_id}')
            
            except Exception as e:
                logger.error(f'Fel vid CS2 toggle: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte ändra status: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(
        name="steam-link",
        description="Länka ditt SteamID till Discord-kontot"
    )
    @app_commands.describe(
        steam_id="Ditt SteamID64 (ex: 76561198012345678)"
    )
    async def steam_link(
        self,
        interaction: discord.Interaction,
        steam_id: str
    ):
        """Länka SteamID till Discord account"""
        
        # Validera SteamID format (SteamID64 är 17 siffror)
        if not steam_id.isdigit() or len(steam_id) != 17:
            await interaction.response.send_message(
                embed=create_error_embed(
                    'Ogiltigt SteamID format! Använd SteamID64 (17 siffror).\n'
                    'Hitta ditt SteamID på: https://steamid.io/'
                ),
                ephemeral=True
            )
            return
        
        async with async_session() as session:
            try:
                # Kolla om redan länkat
                result = await session.execute(
                    select(PlayerSteamID).where(
                        PlayerSteamID.user_id == interaction.user.id
                    )
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    existing.steam_id = steam_id
                    existing.verified = True
                else:
                    new_link = PlayerSteamID(
                        user_id=interaction.user.id,
                        guild_id=interaction.guild_id,
                        steam_id=steam_id,
                        verified=True
                    )
                    session.add(new_link)
                
                await session.commit()
                
                embed = discord.Embed(
                    title="✅ SteamID Länkat!",
                    description=f"Ditt SteamID är nu länkat till ditt Discord-konto",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="🎮 SteamID",
                    value=f"`{steam_id}`",
                    inline=False
                )
                
                embed.set_footer(text="Du kan nu delta i CS2 matcher!")
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                logger.info(f'{interaction.user.name} länkade SteamID {steam_id}')
            
            except Exception as e:
                logger.error(f'Fel vid länkning av SteamID: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte länka SteamID: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(
        name="cs2-status",
        description="[ADMIN] Visa CS2 server status"
    )
    @is_tournament_admin()
    async def cs2_status(self, interaction: discord.Interaction):
        """Visa CS2 server konfiguration och status"""
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(CS2ServerConfig).where(
                        CS2ServerConfig.guild_id == interaction.guild_id
                    )
                )
                config = result.scalar_one_or_none()
                
                if not config:
                    await interaction.response.send_message(
                        embed=create_error_embed(
                            'CS2 server är inte konfigurerad! Använd `/cs2-setup`.'
                        ),
                        ephemeral=True
                    )
                    return
                
                # Hämta antal länkade SteamIDs
                steamid_count = await session.execute(
                    select(PlayerSteamID).where(
                        PlayerSteamID.guild_id == interaction.guild_id
                    )
                )
                total_steamids = len(steamid_count.scalars().all())
                
                # Hämta senaste server logs
                recent_logs = await session.execute(
                    select(MatchServerLog).order_by(
                        MatchServerLog.created_at.desc()
                    ).limit(10)
                )
                logs = recent_logs.scalars().all()
                
                embed = discord.Embed(
                    title="🖥️ CS2 Server Status",
                    color=discord.Color.blue() if config.enabled else discord.Color.red()
                )
                
                status_emoji = "✅" if config.enabled else "❌"
                embed.add_field(
                    name="Status",
                    value=f"{status_emoji} {'Aktiverad' if config.enabled else 'Avaktiverad'}",
                    inline=True
                )
                
                # Visa båda servrarna
                server_ip = os.getenv('CS2_SERVER_IP', config.server_ip)
                server1_port = os.getenv('CS2_SERVER1_PORT', '27015')
                server2_port = os.getenv('CS2_SERVER2_PORT', '27016')
                
                # Kolla vilka servrar som är i bruk
                server1_status = "🟢 Ledig"
                server2_status = "🟢 Ledig"
                
                for match_id, (client, server_num) in self.server_manager.active_servers.items():
                    if server_num == 1:
                        server1_status = f"🔴 Upptagen (Match {match_id})"
                    elif server_num == 2:
                        server2_status = f"🔴 Upptagen (Match {match_id})"
                
                embed.add_field(
                    name="🖥️ Server 1",
                    value=f"`{server_ip}:{server1_port}`\n{server1_status}",
                    inline=True
                )
                
                embed.add_field(
                    name="🖥️ Server 2",
                    value=f"`{server_ip}:{server2_port}`\n{server2_status}",
                    inline=True
                )
                
                embed.add_field(
                    name="👥 Länkade SteamIDs",
                    value=f"{total_steamids} spelare",
                    inline=False
                )
                
                if logs:
                    # Gruppera logs per server
                    server1_logs = [log for log in logs if log.server_num == 1][:3]
                    server2_logs = [log for log in logs if log.server_num == 2][:3]
                    
                    if server1_logs:
                        logs_text = ""
                        for log in server1_logs:
                            status_icon = "✅" if log.config_sent else "❌"
                            logs_text += f"{status_icon} Match {log.match_id} - <t:{int(log.created_at.timestamp())}:R>\n"
                        
                        embed.add_field(
                            name="📋 Server 1 - Senaste Sessions",
                            value=logs_text,
                            inline=True
                        )
                    
                    if server2_logs:
                        logs_text = ""
                        for log in server2_logs:
                            status_icon = "✅" if log.config_sent else "❌"
                            logs_text += f"{status_icon} Match {log.match_id} - <t:{int(log.created_at.timestamp())}:R>\n"
                        
                        embed.add_field(
                            name="📋 Server 2 - Senaste Sessions",
                            value=logs_text,
                            inline=True
                        )
                
                # Lägg till info om concurrent capacity
                embed.set_footer(text="🔄 Systemet kan hantera 2 matcher samtidigt")
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            
            except Exception as e:
                logger.error(f'Fel vid hämtning av CS2 status: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte hämta status: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(
        name="cs2-force-start",
        description="[ADMIN] Tvinga-starta server för en match"
    )
    @app_commands.describe(match_id="Match ID")
    @is_tournament_admin()
    async def cs2_force_start(
        self,
        interaction: discord.Interaction,
        match_id: int
    ):
        """Manuellt starta server för en specifik match"""
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            success = await start_match_server(self.bot, match_id)
            
            if success:
                await interaction.followup.send(
                    embed=create_success_embed(
                        f'✅ Server startad för match {match_id}!'
                    )
                )
            else:
                await interaction.followup.send(
                    embed=create_error_embed(
                        f'❌ Kunde inte starta server för match {match_id}'
                    )
                )
        
        except Exception as e:
            logger.error(f'Fel vid force-start: {e}', exc_info=True)
            await interaction.followup.send(
                embed=create_error_embed(f'Fel: {str(e)}')
            )
    
    @app_commands.command(
        name="cs2-force-stop",
        description="[ADMIN] Tvinga-stoppa server för en match"
    )
    @app_commands.describe(match_id="Match ID")
    @is_tournament_admin()
    async def cs2_force_stop(
        self,
        interaction: discord.Interaction,
        match_id: int
    ):
        """Manuellt stoppa server för en specifik match"""
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            await stop_match_server(self.bot, match_id, delay=0)
            
            await interaction.followup.send(
                embed=create_success_embed(
                    f'✅ Server stoppad för match {match_id}'
                )
            )
        
        except Exception as e:
            logger.error(f'Fel vid force-stop: {e}', exc_info=True)
            await interaction.followup.send(
                embed=create_error_embed(f'Fel: {str(e)}')
            )


async def setup(bot):
    await bot.add_cog(CS2ServerCog(bot))