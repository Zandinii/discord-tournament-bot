import discord
from functools import wraps
from database.database import async_session
from database.models import Guild

TOURNAMENT_ADMIN_ROLE_NAME = "Tournament Admin"

async def has_tournament_admin_role(interaction: discord.Interaction) -> bool:
    """Kolla om användare har Tournament Admin rollen"""
    if interaction.user.guild_permissions.administrator:
        return True
    
    # Kolla om användaren har Tournament Admin rollen
    role = discord.utils.get(interaction.guild.roles, name=TOURNAMENT_ADMIN_ROLE_NAME)
    if role and role in interaction.user.roles:
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

async def setup_tournament_admin_role(guild: discord.Guild) -> discord.Role:
    """Skapa Tournament Admin rollen om den inte finns"""
    role = discord.utils.get(guild.roles, name=TOURNAMENT_ADMIN_ROLE_NAME)
    
    if not role:
        role = await guild.create_role(
            name=TOURNAMENT_ADMIN_ROLE_NAME,
            color=discord.Color.gold(),
            mentionable=True,
            reason="Tournament Bot Admin Role"
        )
    
    return role