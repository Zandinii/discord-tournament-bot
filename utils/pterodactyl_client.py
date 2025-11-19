"""
Pterodactyl Panel API Client
Hanterar all kommunikation med Pterodactyl för CS2 server automation
"""

import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any, List
from asyncio import Throttler

logger = logging.getLogger('TournamentBot.Pterodactyl')


class PterodactylAPIError(Exception):
    """Custom exception för Pterodactyl API errors"""
    pass


class PterodactylClient:
    """
    Asynkron klient för Pterodactyl Panel API
    Hanterar rate limiting, retries och error handling
    """
    
    def __init__(self, panel_url: str, api_key: str, server_uuid: str):
        self.panel_url = panel_url.rstrip('/')
        self.api_key = api_key
        self.server_uuid = server_uuid
        self.base_url = f"{self.panel_url}/api/client/servers/{server_uuid}"
        
        # Rate limiter: Max 120 requests per minut
        self.throttler = Throttler(rate_limit=120, period=60)
        
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        json_data: Optional[Dict] = None,
        retries: int = 3,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Gör en API request med retry logic och rate limiting
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(retries):
            try:
                async with self.throttler:
                    async with aiohttp.ClientSession() as session:
                        async with session.request(
                            method, 
                            url, 
                            headers=self.headers,
                            json=json_data,
                            timeout=aiohttp.ClientTimeout(total=timeout)
                        ) as response:
                            
                            if response.status == 429:
                                # Rate limited
                                retry_after = int(response.headers.get('Retry-After', 60))
                                logger.warning(f'Rate limited. Väntar {retry_after}s')
                                await asyncio.sleep(retry_after)
                                continue
                            
                            if response.status == 500:
                                # Server error, retry
                                if attempt < retries - 1:
                                    wait_time = 2 ** attempt
                                    logger.warning(f'Server error 500. Retry {attempt+1}/{retries} om {wait_time}s')
                                    await asyncio.sleep(wait_time)
                                    continue
                                else:
                                    raise PterodactylAPIError(f'Server error 500 efter {retries} försök')
                            
                            if response.status >= 400:
                                error_text = await response.text()
                                raise PterodactylAPIError(
                                    f'API Error {response.status}: {error_text}'
                                )
                            
                            # Success
                            return await response.json()
            
            except asyncio.TimeoutError:
                if attempt < retries - 1:
                    logger.warning(f'Timeout. Retry {attempt+1}/{retries}')
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise PterodactylAPIError(f'Timeout efter {retries} försök')
            
            except aiohttp.ClientError as e:
                if attempt < retries - 1:
                    logger.warning(f'Client error: {e}. Retry {attempt+1}/{retries}')
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise PterodactylAPIError(f'Client error: {str(e)}')
        
        raise PterodactylAPIError('Nådde max retries')
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Hämta server status"""
        try:
            response = await self._request('GET', '/resources')
            return response.get('attributes', {})
        except Exception as e:
            logger.error(f'Fel vid hämtning av server status: {e}')
            raise
    
    async def start_server(self) -> bool:
        """
        Starta servern
        Returns: True om kommandot skickades
        """
        try:
            await self._request('POST', '/power', json_data={'signal': 'start'})
            logger.info(f'Start-kommando skickat till server {self.server_uuid}')
            return True
        except Exception as e:
            logger.error(f'Fel vid start av server: {e}')
            return False
    
    async def stop_server(self) -> bool:
        """
        Stoppa servern
        Returns: True om kommandot skickades
        """
        try:
            await self._request('POST', '/power', json_data={'signal': 'stop'})
            logger.info(f'Stop-kommando skickat till server {self.server_uuid}')
            return True
        except Exception as e:
            logger.error(f'Fel vid stopp av server: {e}')
            return False
    
    async def restart_server(self) -> bool:
        """Restarta servern"""
        try:
            await self._request('POST', '/power', json_data={'signal': 'restart'})
            logger.info(f'Restart-kommando skickat till server {self.server_uuid}')
            return True
        except Exception as e:
            logger.error(f'Fel vid restart av server: {e}')
            return False
    
    async def send_command(self, command: str) -> bool:
        """
        Skicka console-kommando till servern
        OBS: Servern måste vara igång!
        """
        try:
            await self._request(
                'POST', 
                '/command',
                json_data={'command': command}
            )
            logger.info(f'Kommando skickat: {command}')
            return True
        except Exception as e:
            logger.error(f'Fel vid sändning av kommando "{command}": {e}')
            return False
    
    async def send_commands_batch(self, commands: List[str], delay: float = 0.5) -> int:
        """
        Skicka flera kommandon i sekvens med delay mellan
        Returns: Antal lyckade kommandon
        """
        success_count = 0
        for cmd in commands:
            if await self.send_command(cmd):
                success_count += 1
            await asyncio.sleep(delay)
        return success_count
    
    async def wait_for_running(self, timeout: int = 180, poll_interval: int = 5) -> bool:
        """
        Vänta tills servern är i 'running' state
        
        Args:
            timeout: Max tid att vänta (sekunder)
            poll_interval: Tid mellan status-checks (sekunder)
        
        Returns: True om servern är running, False om timeout
        """
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                status = await self.get_server_status()
                current_state = status.get('current_state', 'unknown')
                
                logger.info(f'Server state: {current_state}')
                
                if current_state == 'running':
                    logger.info('✅ Server är running!')
                    return True
                
                await asyncio.sleep(poll_interval)
            
            except Exception as e:
                logger.error(f'Fel vid polling av server status: {e}')
                await asyncio.sleep(poll_interval)
        
        logger.warning(f'⏰ Timeout: Server nådde inte running state efter {timeout}s')
        return False
    
    async def get_console_logs(self, lines: int = 100) -> Optional[str]:
        """
        Hämta console logs
        OBS: Kräver ofta WebSocket - Detta är en placeholder
        """
        # Note: Pterodactyl använder WebSocket för live console
        # Detta är en förenklad implementation
        logger.warning('Console logs via REST API är begränsad - använd WebSocket för live logs')
        return None


# Convenience functions för enkel användning

async def create_pterodactyl_client(
    panel_url: str, 
    api_key: str, 
    server_uuid: str
) -> PterodactylClient:
    """Factory function för att skapa klient"""
    return PterodactylClient(panel_url, api_key, server_uuid)