# tests/test_cs2_server_manager.py
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from utils.cs2_server_manager import CS2ServerManager
from database.models import Match, Tournament, CS2ServerConfig


@pytest.mark.asyncio
async def test_get_player_steamids_1v1():
    """Test hämtning av SteamIDs för 1v1 match"""
    bot = MagicMock()
    manager = CS2ServerManager(bot)
    
    # Mock database data
    mock_match = Match(
        id=1,
        participant1_id=100,
        participant2_id=200
    )
    
    with patch('utils.cs2_server_manager.async_session'):
        steamids = await manager.get_player_steamids(1)
        
        # Verifiera att rätt spelare hämtades
        assert 100 in steamids or 200 in steamids


@pytest.mark.asyncio
async def test_generate_match_config():
    """Test generering av match config commands"""
    bot = MagicMock()
    manager = CS2ServerManager(bot)
    
    mock_match = Match(id=1, maps_to_play='[{"map": "de_dust2", "side_p1": "CT"}]')
    mock_tournament = Tournament(game_mode='1v1')
    mock_steamids = {
        100: '76561198012345678',
        200: '76561198087654321'
    }
    
    commands = await manager.generate_match_config(
        mock_match, 
        mock_tournament, 
        mock_steamids
    )
    
    # Verifiera att viktiga kommandon finns
    assert any('mp_maxrounds' in cmd for cmd in commands)
    assert any('changelevel de_dust2' in cmd for cmd in commands)
    assert any('sv_password' in cmd for cmd in commands)


@pytest.mark.asyncio
async def test_setup_match_server_no_config():
    """Test att setup misslyckas om ingen config finns"""
    bot = MagicMock()
    manager = CS2ServerManager(bot)
    
    with patch.object(manager, 'get_server_config', return_value=None):
        result = await manager.setup_match_server(1)
        assert result == False