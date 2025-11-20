"""
CS2 Server Manager
Hanterar automatisk server-start, konfiguration och match-setup
MED STÖD FÖR FLERA SERVRAR
"""

import asyncio
import logging
import json
import os
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy import select
import discord

from utils.pterodactyl_client import PterodactylClient, PterodactylAPIError
from database.database import async_session
from database.models import (
    Match, MatchServerLog, CS2ServerConfig, PlayerSteamID,
    Team, TeamMember, Tournament
)

logger = logging.getLogger('TournamentBot.CS2ServerManager')


class CS2ServerManager:
    """
    Manager för CS2 server automation med multi-server stöd
    Hanterar hela flödet från server-start till match-setup
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.active_servers: Dict[int, Tuple[PterodactylClient, int]] = {}  # match_id: (client, server_num)
        self.server_locks: Dict[int, asyncio.Lock] = {1: asyncio.Lock(), 2: asyncio.Lock()}
        self.server_in_use: Dict[int, Optional[int]] = {1: None, 2: None}  # server_num: match_id
    
    async def get_server_config(self, guild_id: int) -> Optional[CS2ServerConfig]:
        """Hämta server-konfiguration för guild"""
        async with async_session() as session:
            result = await session.execute(
                select(CS2ServerConfig).where(
                    CS2ServerConfig.guild_id == guild_id,
                    CS2ServerConfig.enabled == True
                )
            )
            return result.scalar_one_or_none()
    
    async def get_available_server(self) -> Optional[int]:
        """
        Hitta en ledig server
        Returns: Server nummer (1 eller 2) eller None om alla upptagna
        """
        for server_num in [1, 2]:
            lock = self.server_locks[server_num]
            if not lock.locked():
                # Kolla om servern faktiskt är ledig
                if self.server_in_use[server_num] is None:
                    return server_num
        
        # Ingen server ledig
        return None
    
    async def acquire_server(self, match_id: int) -> Optional[int]:
        """
        Försök få tillgång till en ledig server
        Returns: Server nummer eller None
        """
        server_num = await self.get_available_server()
        if server_num is None:
            logger.warning(f'⏳ Alla servrar upptagna, väntar på ledig server för match {match_id}')
            # Vänta max 5 minuter på att en server ska bli ledig
            timeout = 300
            start_time = asyncio.get_event_loop().time()
            
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                await asyncio.sleep(10)
                server_num = await self.get_available_server()
                if server_num is not None:
                    break
            
            if server_num is None:
                logger.error(f'❌ Timeout: Ingen server blev ledig för match {match_id}')
                return None
        
        # Lås servern
        await self.server_locks[server_num].acquire()
        self.server_in_use[server_num] = match_id
        logger.info(f'🔒 Server {server_num} tilldelad till match {match_id}')
        return server_num
    
    async def release_server(self, match_id: int, server_num: int):
        """Frigör en server efter användning"""
        try:
            if self.server_in_use.get(server_num) == match_id:
                self.server_in_use[server_num] = None
                self.server_locks[server_num].release()
                logger.info(f'🔓 Server {server_num} frigjord från match {match_id}')
        except Exception as e:
            logger.error(f'Fel vid frigörning av server: {e}')
    
    async def create_pterodactyl_client(
        self, 
        server_num: int, 
        config: CS2ServerConfig
    ) -> PterodactylClient:
        """
        Skapa Pterodactyl client för specifik server
        """
        from utils.pterodactyl_client import create_pterodactyl_client
        
        # Hämta rätt UUID från env
        server_uuid_key = f'PTERO_SERVER{server_num}_UUID'
        server_uuid = os.getenv(server_uuid_key)
        
        if not server_uuid:
            raise ValueError(f'Miljövariabel {server_uuid_key} saknas!')
        
        return await create_pterodactyl_client(
            panel_url=config.ptero_panel_url or os.getenv('PTERO_PANEL_URL'),
            api_key=os.getenv('PTERO_API_KEY'),
            server_uuid=server_uuid
        )
    
    def get_server_port(self, server_num: int) -> int:
        """Hämta rätt port för server"""
        port_key = f'CS2_SERVER{server_num}_PORT'
        port = os.getenv(port_key)
        return int(port) if port else (27015 if server_num == 1 else 27016)
    
    async def get_player_steamids(self, match_id: int) -> Dict[int, str]:
        """
        Hämta SteamIDs för alla spelare i en match
        Returns: {user_id: steam_id}
        """
        async with async_session() as session:
            # Hämta match
            match = await session.get(Match, match_id)
            if not match:
                return {}
            
            # Hämta turnering för att se om det är team-match
            tournament = await session.get(Tournament, match.tournament_id)
            is_team = tournament.game_mode in ['2v2', '5v5']
            
            user_ids = []
            
            if is_team:
                # Hämta alla team members från båda lagen
                for participant_id in [match.participant1_id, match.participant2_id]:
                    if participant_id:
                        members_result = await session.execute(
                            select(TeamMember).where(TeamMember.team_id == participant_id)
                        )
                        for member in members_result.scalars().all():
                            user_ids.append(member.user_id)
            else:
                # 1v1 - bara två spelare
                user_ids = [match.participant1_id, match.participant2_id]
            
            # Hämta SteamIDs
            steamids = {}
            for user_id in user_ids:
                if user_id:
                    steam_result = await session.execute(
                        select(PlayerSteamID).where(PlayerSteamID.user_id == user_id)
                    )
                    steam = steam_result.scalar_one_or_none()
                    if steam:
                        steamids[user_id] = steam.steam_id
            
            return steamids
    
    async def generate_match_config(
        self, 
        match: Match, 
        tournament: Tournament,
        steamids: Dict[int, str]
    ) -> List[str]:
        """
        Generera CS2 console-kommandon för match-setup
        
        Returns: Lista av console-kommandon
        """
        commands = []
        
        # Basic server setup
        commands.extend([
            'sv_cheats 0',
            'mp_autoteambalance 0',
            'mp_limitteams 0',
            'mp_teamname_1 "Team A"',
            'mp_teamname_2 "Team B"',
        ])
        
        # Match settings baserat på BO format
        maps_data = json.loads(match.maps_to_play) if match.maps_to_play else []
        
        if maps_data:
            first_map = maps_data[0]['map']
            commands.append(f'changelevel {first_map}')
        
        # Overtime settings
        commands.extend([
            'mp_overtime_enable 1',
            'mp_overtime_maxrounds 6',
            'mp_overtime_startmoney 10000',
        ])
        
        # Round settings (MR12 default för CS2)
        commands.extend([
            'mp_maxrounds 24',
            'mp_roundtime 1.92',
            'mp_roundtime_defuse 1.92',
            'mp_freezetime 15',
            'mp_warmup_pausetimer 1',
            'mp_warmuptime 60',
        ])
        
        # Knife round om konfigurerat
        commands.extend([
            'mp_do_warmup_period 1',
            'mp_warmuptime 60',
        ])
        
        # Password
        if tournament:
            async with async_session() as session:
                config = await self.get_server_config(tournament.guild_id)
                if config and config.server_password:
                    commands.append(f'sv_password "{config.server_password}"')
        
        # SteamID Whitelist
        if steamids:
            commands.append('# SteamID Whitelist')
            for user_id, steam_id in steamids.items():
                commands.append(f'# Allow: {steam_id}')
        
        return commands
    
    async def setup_match_server(self, match_id: int) -> bool:
        """
        Huvudfunktion: Sätt upp server för en match
        
        Flöde:
        1. Hitta ledig server
        2. Starta server
        3. Vänta tills running
        4. Konfigurera match
        5. Notifiera spelare
        
        Returns: True om success
        """
        server_num = None
        try:
            async with async_session() as session:
                # Hämta match
                match = await session.get(Match, match_id)
                if not match:
                    logger.error(f'Match {match_id} hittades inte')
                    return False
                
                # Hämta tournament
                tournament = await session.get(Tournament, match.tournament_id)
                if not tournament:
                    logger.error(f'Tournament {match.tournament_id} hittades inte')
                    return False
                
                # Hämta server config
                config = await self.get_server_config(tournament.guild_id)
                if not config:
                    logger.error(f'Ingen CS2 server config för guild {tournament.guild_id}')
                    return False
                
                # STEG 1: Hitta och låsa en ledig server
                server_num = await self.acquire_server(match_id)
                if server_num is None:
                    logger.error(f'❌ Ingen server tillgänglig för match {match_id}')
                    return False
                
                # Skapa Pterodactyl client för rätt server
                ptero_client = await self.create_pterodactyl_client(server_num, config)
                self.active_servers[match_id] = (ptero_client, server_num)
                
                # Skapa server log
                server_log = MatchServerLog(
                    match_id=match_id,
                    server_num=server_num  # Spara vilket server som används
                )
                session.add(server_log)
                await session.commit()
                await session.refresh(server_log)
                
                logger.info(f'🚀 Startar CS2 Server {server_num} för match {match_id}...')
                
                # STEG 2: STARTA SERVER
                if not await ptero_client.start_server():
                    server_log.errors = f'Kunde inte starta server {server_num}'
                    await session.commit()
                    await self.release_server(match_id, server_num)
                    return False
                
                server_log.server_started_at = datetime.utcnow()
                await session.commit()
                
                # STEG 3: VÄNTA TILLS SERVER ÄR RUNNING
                logger.info(f'⏳ Väntar på att Server {server_num} ska bli redo...')
                if not await ptero_client.wait_for_running(timeout=180, poll_interval=5):
                    server_log.errors = f'Server {server_num} timeout - blev inte running'
                    await session.commit()
                    await self.release_server(match_id, server_num)
                    return False
                
                server_log.server_ready_at = datetime.utcnow()
                await session.commit()
                
                # Extra väntetid för att server ska initiera helt
                await asyncio.sleep(10)
                
                # STEG 4: HÄMTA STEAMIDS
                steamids = await self.get_player_steamids(match_id)
                if not steamids:
                    logger.warning(f'⚠️ Inga SteamIDs hittades för match {match_id}')
                
                server_log.players_connected = json.dumps(list(steamids.values()))
                await session.commit()
                
                # STEG 5: GENERERA & SKICKA MATCH CONFIG
                logger.info(f'⚙️ Konfigurerar match på Server {server_num}...')
                commands = await self.generate_match_config(match, tournament, steamids)
                
                success_count = await ptero_client.send_commands_batch(commands, delay=0.5)
                logger.info(f'📤 Skickade {success_count}/{len(commands)} kommandon')
                
                server_log.config_sent = True
                await session.commit()
                
                # STEG 6: NOTIFIERA SPELARE
                server_port = self.get_server_port(server_num)
                await self.notify_players(match, config, server_num, server_port)
                
                logger.info(f'✅ Server {server_num} setup komplett för match {match_id}')
                return True
        
        except Exception as e:
            logger.error(f'❌ Fel vid server setup för match {match_id}: {e}', exc_info=True)
            
            # Frigör server om något gick fel
            if server_num:
                await self.release_server(match_id, server_num)
            
            # Logga error i databas
            try:
                async with async_session() as session:
                    server_log = await session.execute(
                        select(MatchServerLog).where(MatchServerLog.match_id == match_id)
                    )
                    log = server_log.scalar_one_or_none()
                    if log:
                        log.errors = str(e)
                        await session.commit()
            except:
                pass
            
            return False
    
    async def notify_players(
        self, 
        match: Match, 
        config: CS2ServerConfig, 
        server_num: int,
        server_port: int
    ):
        """
        Skicka connect-info till spelare via Discord voice channel text chats
        """
        try:
            guild = self.bot.get_guild(match.tournament.guild_id)
            if not guild:
                return
            
            server_ip = os.getenv('CS2_SERVER_IP', config.server_ip)
            connect_string = f"connect {server_ip}:{server_port}"
            if config.server_password:
                connect_string += f"; password {config.server_password}"
            
            embed = discord.Embed(
                title=f"🎮 Server {server_num} Redo!",
                description=f"CS2-servern är redo för match!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📡 Connect",
                value=f"```{connect_string}```",
                inline=False
            )
            
            embed.add_field(
                name="ℹ️ Info",
                value=f"Server: `{server_ip}:{server_port}` (Server #{server_num})\n"
                      f"Password: `{config.server_password or 'Ingen'}`",
                inline=False
            )
            
            embed.set_footer(text="Lycka till! 🍀")
            
            # Skicka till båda teams voice channels
            for channel_id in [match.voice_channel_1_id, match.voice_channel_2_id]:
                if channel_id:
                    channel = guild.get_channel(channel_id)
                    if channel:
                        await channel.send(embed=embed)
        
        except Exception as e:
            logger.error(f'Fel vid notifiering av spelare: {e}')
    
    async def shutdown_match_server(self, match_id: int, delay: int = 0):
        """
        Stäng ner server efter match
        
        Args:
            match_id: Match ID
            delay: Sekunder att vänta innan shutdown (för att spelare ska kunna se resultat)
        """
        try:
            if delay > 0:
                logger.info(f'⏰ Väntar {delay}s innan server shutdown...')
                await asyncio.sleep(delay)
            
            server_info = self.active_servers.get(match_id)
            if not server_info:
                logger.warning(f'Ingen aktiv server för match {match_id}')
                return
            
            client, server_num = server_info
            
            logger.info(f'🔴 Stänger ner Server {server_num} för match {match_id}')
            
            # Skicka varning till spelare först
            await client.send_command('say "Server stängs ner om 30 sekunder..."')
            await asyncio.sleep(30)
            
            # Stoppa server
            await client.stop_server()
            
            # Uppdatera log
            async with async_session() as session:
                result = await session.execute(
                    select(MatchServerLog).where(MatchServerLog.match_id == match_id)
                )
                log = result.scalar_one_or_none()
                if log:
                    log.server_stopped_at = datetime.utcnow()
                    await session.commit()
            
            # Frigör server
            await self.release_server(match_id, server_num)
            
            # Ta bort från active servers
            del self.active_servers[match_id]
            
            logger.info(f'✅ Server {server_num} shutdown komplett för match {match_id}')
        
        except Exception as e:
            logger.error(f'Fel vid server shutdown: {e}', exc_info=True)


# Helper functions

async def start_match_server(bot, match_id: int) -> bool:
    """Convenience function för att starta match server"""
    manager = CS2ServerManager(bot)
    return await manager.setup_match_server(match_id)


async def stop_match_server(bot, match_id: int, delay: int = 300):
    """Convenience function för att stoppa match server"""
    manager = CS2ServerManager(bot)
    await manager.shutdown_match_server(match_id, delay)