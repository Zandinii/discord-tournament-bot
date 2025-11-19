# tests/test_integration_full_match.py
import asyncio
import discord
import pytest
from unittest.mock import AsyncMock, patch
from discord.ext import commands


@pytest.mark.asyncio
async def test_full_match_flow():
    """
    Test hela flödet från match creation till server shutdown
    """
    # Setup mock bot
    bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())
    
    # Mock Pterodactyl API responses
    with patch('utils.pterodactyl_client.aiohttp.ClientSession') as mock_session:
        # Mock successful server start
        mock_session.return_value.__aenter__.return_value.request.return_value.__aenter__.return_value.status = 200
        
        # 1. Skapa match
        match_id = 1  # Mock match ID
        
        # 2. Trigga match_created event
        bot.dispatch('match_created', match_id)
        await asyncio.sleep(2)  # Vänta på event handling
        
        # 3. Verifiera att server startades
        # (Kontrollera database logs)
        
        # 4. Simulera match completion
        bot.dispatch('match_completed', match_id)
        await asyncio.sleep(2)
        
        # 5. Verifiera att server stoppades
        # (Kontrollera database logs)