# tests/test_pterodactyl_client.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from utils.pterodactyl_client import PterodactylClient, PterodactylAPIError


@pytest.mark.asyncio
async def test_start_server_success():
    """Test att start_server skickar korrekt request"""
    client = PterodactylClient(
        panel_url="https://test.panel.com",
        api_key="test_key",
        server_uuid="test_uuid"
    )
    
    with patch.object(client, '_request', return_value={'success': True}) as mock_request:
        result = await client.start_server()
        
        assert result == True
        mock_request.assert_called_once_with(
            'POST', 
            '/power', 
            json_data={'signal': 'start'}
        )


@pytest.mark.asyncio
async def test_wait_for_running_timeout():
    """Test att timeout fungerar korrekt"""
    client = PterodactylClient(
        panel_url="https://test.panel.com",
        api_key="test_key",
        server_uuid="test_uuid"
    )
    
    async def mock_status():
        return {'current_state': 'starting'}
    
    client.get_server_status = mock_status
    
    result = await client.wait_for_running(timeout=5, poll_interval=1)
    assert result == False


@pytest.mark.asyncio
async def test_send_commands_batch():
    """Test batch command sending"""
    client = PterodactylClient(
        panel_url="https://test.panel.com",
        api_key="test_key",
        server_uuid="test_uuid"
    )
    
    commands = ['mp_maxrounds 24', 'mp_roundtime 1.92']
    
    with patch.object(client, 'send_command', return_value=True) as mock_send:
        count = await client.send_commands_batch(commands, delay=0.1)
        
        assert count == 2
        assert mock_send.call_count == 2


@pytest.mark.asyncio
async def test_rate_limiting():
    """Test att rate limiting fungerar"""
    client = PterodactylClient(
        panel_url="https://test.panel.com",
        api_key="test_key",
        server_uuid="test_uuid"
    )
    
    # Simulera många requests
    async def mock_request(*args, **kwargs):
        return {'status': 'ok'}
    
    client._request = mock_request
    
    start = asyncio.get_event_loop().time()
    
    # Skicka 130 requests (över rate limit på 120/min)
    tasks = [client.get_server_status() for _ in range(130)]
    await asyncio.gather(*tasks)
    
    elapsed = asyncio.get_event_loop().time() - start
    
    # Bör ta minst 60 sekunder pga rate limiting
    assert elapsed >= 60

