import discord
from functools import wraps

def is_admin():
    """Decorator för att kräva admin-rättigheter"""
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Du behöver administratörs-rättigheter för detta kommando!",
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
        interaction.user.guild_permissions.administrator or
        interaction.user.id == tournament.created_by
    )