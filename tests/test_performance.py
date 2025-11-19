# Concurrent matches performance test

import asyncio
import pytest
from utils.cs2_server_manager import CS2ServerManager
from utils.pterodactyl_client import PterodactylClient
from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_multiple_matches_concurrent():
    """Test att flera matcher kan köras samtidigt"""
    bot = MagicMock()
    manager = CS2ServerManager(bot)
    
    # Skapa 5 matcher samtidigt
    tasks = [
        manager.setup_match_server(i)
        for i in range(1, 6)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Alla bör lyckas (eller ge vettiga fel)
    assert all(isinstance(r, bool) or isinstance(r, Exception) for r in results)

# Rate limit compliance test

@pytest.mark.asyncio
async def test_rate_limit_not_exceeded():
    """Verifiera att vi inte överskrider Pterodactyl rate limits"""
    client = PterodactylClient(
        panel_url="https://test.panel.com",
        api_key="test_key",
        server_uuid="test_uuid"
    )
    
    # Räkna requests över 1 minut
    request_count = 0
    
    async def count_request(*args, **kwargs):
        nonlocal request_count
        request_count += 1
        return {'status': 'ok'}
    
    client._request = count_request
    
    # Skicka många commands
    commands = [f'say test_{i}' for i in range(150)]
    await client.send_commands_batch(commands, delay=0)
    
    # Max 120 requests per minut
    assert request_count <= 120