# tests/mock_pterodactyl_server.py
import asyncio
import pytest
from aiohttp import web
import json


class MockPterodactylServer:
    """Mock Pterodactyl API server för tester"""
    
    def __init__(self):
        self.server_state = 'stopped'
        self.commands_received = []
    
    async def handle_power(self, request):
        data = await request.json()
        signal = data.get('signal')
        
        if signal == 'start':
            self.server_state = 'starting'
        elif signal == 'stop':
            self.server_state = 'stopping'
        
        return web.json_response({'success': True})
    
    async def handle_resources(self, request):
        return web.json_response({
            'attributes': {
                'current_state': self.server_state
            }
        })
    
    async def handle_command(self, request):
        data = await request.json()
        command = data.get('command')
        self.commands_received.append(command)
        return web.json_response({'success': True})
    
    def create_app(self):
        app = web.Application()
        app.router.add_post('/api/client/servers/{uuid}/power', self.handle_power)
        app.router.add_get('/api/client/servers/{uuid}/resources', self.handle_resources)
        app.router.add_post('/api/client/servers/{uuid}/command', self.handle_command)
        return app


@pytest.fixture
async def mock_panel():
    """Fixture för mock Pterodactyl server"""
    mock = MockPterodactylServer()
    app = mock.create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    
    yield mock
    
    await runner.cleanup()