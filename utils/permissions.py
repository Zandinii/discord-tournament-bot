import discord
from functools import wraps
from database.database import async_session
from database.models import Guild

async def has_tournament_admin_role(interaction: discord.Interaction) -> bool:
    """
    Kolla om användare har Tournament Admin rättigheter
    Returnerar True om användaren har:
    1. Administrator Discord-permission, ELLER
    2. Den specifika admin-rollen som är konfigurerad för servern
    """
    # 1. Kolla Discord Administrator permission
    if interaction.user.guild_permissions.administrator:
        return True
    
    # 2. Kolla specifik admin roll från databas
    async with async_session() as session:
        guild_config = await session.get(Guild, interaction.guild_id)
        
        if guild_config and guild_config.admin_role_id:
            # Kolla om användaren har den konfigurerade admin-rollen
            admin_role = interaction.guild.get_role(guild_config.admin_role_id)
            if admin_role and admin_role in interaction.user.roles:
                return True
    
    return False

def is_tournament_admin():
    """Decorator för att kräva Tournament Admin rättigheter"""
    async def predicate(interaction: discord.Interaction) -> bool:
        if await has_tournament_admin_role(interaction):
            return True
        
        await interaction.response.send_message(
            "❌ Du behöver **Tournament Admin** rollen eller Administrator-rättigheter för detta kommando!",
            ephemeral=True
        )
        return False
    
    return discord.app_commands.check(predicate)

def is_admin():
    """Decorator för att kräva admin-rättigheter (behåll för bakåtkompatibilitet)"""
    return is_tournament_admin()

def is_server_admin():
    """Decorator för server-admin endast (setup-kommandon etc)"""
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Du behöver Server Administrator-rättigheter för detta kommando!",
                ephemeral=True
            )
            return False
        return True
    return discord.app_commands.check(predicate)

def is_tournament_creator():
    """Check om användaren skapade turneringen"""
    async def predicate(interaction: discord.Interaction) -> bool:
        # Detta implementeras senare när vi har tournament context
        return True
    return discord.app_commands.check(predicate)

async def has_role(interaction: discord.Interaction, role_id: int) -> bool:
    """Kolla om användare har en specifik roll"""
    member = interaction.user
    return any(role.id == role_id for role in member.roles)

async def can_manage_tournament(interaction: discord.Interaction, tournament) -> bool:
    """Kolla om användare kan hantera turnering"""
    return (
        await has_tournament_admin_role(interaction) or
        interaction.user.id == tournament.created_by
    )