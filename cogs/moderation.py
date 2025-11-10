import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Literal
from datetime import datetime, timedelta
from database.database import async_session
from database.models import (
    PlayerWarning, PlayerBan, Player, Guild
)
from utils.permissions import is_tournament_admin
from utils.embeds import create_error_embed, create_success_embed
from sqlalchemy import select, and_, desc
import logging

logger = logging.getLogger('TournamentBot.Moderation')

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.moderation_embed_message_id = {}  # guild_id: message_id
    
    async def update_moderation_embed(self, guild_id: int):
        """Uppdatera moderation embed i tournament-log kanalen"""
        try:
            async with async_session() as session:
                guild_config = await session.get(Guild, guild_id)
                
                if not guild_config or not guild_config.moderation_channel_id:
                    logger.warning(f'Ingen moderation channel satt för guild {guild_id}')
                    return
                
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    return
                
                channel = guild.get_channel(guild_config.moderation_channel_id)
                if not channel:
                    return
                
                # Hämta aktiva varningar
                warnings_result = await session.execute(
                    select(PlayerWarning, Player).join(
                        Player, PlayerWarning.user_id == Player.user_id
                    ).where(
                        PlayerWarning.guild_id == guild_id,
                        PlayerWarning.active == True
                    ).order_by(desc(PlayerWarning.issued_at))
                )
                warnings = warnings_result.all()
                
                # Hämta aktiva bans
                bans_result = await session.execute(
                    select(PlayerBan, Player).join(
                        Player, PlayerBan.user_id == Player.user_id
                    ).where(
                        PlayerBan.guild_id == guild_id,
                        PlayerBan.active == True
                    ).order_by(desc(PlayerBan.issued_at))
                )
                bans = bans_result.all()
                
                # Skapa embed
                embed = discord.Embed(
                    title="🛡️ Moderation Log",
                    description="Aktiva varningar och avstängningar",
                    color=discord.Color.orange(),
                    timestamp=datetime.utcnow()
                )
                
                # Varningar
                if warnings:
                    warnings_text = ""
                    for warning, player in warnings[:10]:  # Max 10
                        warnings_text += (
                            f"**{player.username}** (<@{player.user_id}>)\n"
                            f"├ Anledning: {warning.reason}\n"
                            f"├ Av: <@{warning.issued_by}>\n"
                            f"└ <t:{int(warning.issued_at.timestamp())}:R>\n\n"
                        )
                    
                    embed.add_field(
                        name=f"⚠️ Aktiva Varningar ({len(warnings)})",
                        value=warnings_text or "Inga varningar",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="⚠️ Aktiva Varningar (0)",
                        value="*Inga aktiva varningar*",
                        inline=False
                    )
                
                # Bans
                if bans:
                    bans_text = ""
                    for ban, player in bans[:10]:  # Max 10
                        ban_info = ""
                        if ban.ban_type == 'temporary':
                            remaining = ban.tournaments_banned - ban.tournaments_served
                            ban_info = f"Turneringar kvar: {remaining}"
                        elif ban.expires_at:
                            ban_info = f"Slutar: <t:{int(ban.expires_at.timestamp())}:R>"
                        else:
                            ban_info = "Permanent"
                        
                        bans_text += (
                            f"**{player.username}** (<@{player.user_id}>)\n"
                            f"├ Anledning: {ban.reason}\n"
                            f"├ Typ: {ban_info}\n"
                            f"├ Av: <@{ban.issued_by}>\n"
                            f"└ <t:{int(ban.issued_at.timestamp())}:R>\n\n"
                        )
                    
                    embed.add_field(
                        name=f"🚫 Aktiva Avstängningar ({len(bans)})",
                        value=bans_text or "Inga avstängningar",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="🚫 Aktiva Avstängningar (0)",
                        value="*Inga aktiva avstängningar*",
                        inline=False
                    )
                
                embed.set_footer(text="Uppdateras automatiskt")
                
                # Uppdatera eller skapa meddelande
                message_id = self.moderation_embed_message_id.get(guild_id)
                
                if message_id:
                    try:
                        message = await channel.fetch_message(message_id)
                        await message.edit(embed=embed)
                    except discord.NotFound:
                        # Meddelandet hittades inte, skapa nytt
                        message = await channel.send(embed=embed)
                        self.moderation_embed_message_id[guild_id] = message.id
                else:
                    # Försök hitta befintligt meddelande
                    async for message in channel.history(limit=50):
                        if message.author == self.bot.user and message.embeds:
                            if message.embeds[0].title == "🛡️ Moderation Log":
                                await message.edit(embed=embed)
                                self.moderation_embed_message_id[guild_id] = message.id
                                return
                    
                    # Inget meddelande hittades, skapa nytt
                    message = await channel.send(embed=embed)
                    self.moderation_embed_message_id[guild_id] = message.id
        
        except Exception as e:
            logger.error(f'Fel vid uppdatering av moderation embed: {e}', exc_info=True)
    
    async def check_auto_ban(self, user_id: int, guild_id: int):
        """Kolla om användare ska auto-bannas efter 3 varningar"""
        async with async_session() as session:
            try:
                # Räkna aktiva varningar
                warnings_count = await session.execute(
                    select(PlayerWarning).where(
                        PlayerWarning.user_id == user_id,
                        PlayerWarning.guild_id == guild_id,
                        PlayerWarning.active == True
                    )
                )
                warnings = len(warnings_count.scalars().all())
                
                if warnings >= 3:
                    # Auto-ban för 2 turneringar
                    ban = PlayerBan(
                        user_id=user_id,
                        guild_id=guild_id,
                        reason="Automatisk avstängning: 3 varningar",
                        issued_by=self.bot.user.id,
                        ban_type='temporary',
                        tournaments_banned=2,
                        tournaments_served=0
                    )
                    session.add(ban)
                    
                    # Deaktivera alla varningar
                    warnings_to_deactivate = await session.execute(
                        select(PlayerWarning).where(
                            PlayerWarning.user_id == user_id,
                            PlayerWarning.guild_id == guild_id,
                            PlayerWarning.active == True
                        )
                    )
                    for warning in warnings_to_deactivate.scalars().all():
                        warning.active = False
                    
                    await session.commit()
                    
                    logger.info(f'Auto-ban: User {user_id} avstängd för 2 turneringar efter 3 varningar')
                    
                    # Uppdatera embed
                    await self.update_moderation_embed(guild_id)
                    
                    return True
                
                return False
                
            except Exception as e:
                logger.error(f'Fel vid check av auto-ban: {e}', exc_info=True)
                return False
    
    async def is_user_banned(self, user_id: int, guild_id: int) -> tuple[bool, Optional[str]]:
        """
        Kolla om användare är bannad
        Returns: (is_banned, reason)
        """
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(PlayerBan).where(
                        PlayerBan.user_id == user_id,
                        PlayerBan.guild_id == guild_id,
                        PlayerBan.active == True
                    )
                )
                ban = result.scalar_one_or_none()
                
                if not ban:
                    return False, None
                
                # Kolla om tid-baserad ban har gått ut
                if ban.expires_at and ban.expires_at < datetime.utcnow():
                    ban.active = False
                    await session.commit()
                    await self.update_moderation_embed(guild_id)
                    return False, None
                
                # Bygg reason text
                reason = ban.reason
                if ban.ban_type == 'temporary':
                    remaining = ban.tournaments_banned - ban.tournaments_served
                    reason += f" ({remaining} turneringar kvar)"
                elif ban.expires_at:
                    reason += f" (slutar <t:{int(ban.expires_at.timestamp())}:R>)"
                else:
                    reason += " (permanent)"
                
                return True, reason
                
            except Exception as e:
                logger.error(f'Fel vid check av ban: {e}', exc_info=True)
                return False, None
    
    @app_commands.command(name="warn", description="[ADMIN] Varna en spelare")
    @app_commands.describe(
        user="Spelaren att varna",
        reason="Anledning för varningen"
    )
    @is_tournament_admin()
    async def warn_player(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        reason: str
    ):
        """Varna en spelare"""
        
        if user.bot:
            await interaction.response.send_message(
                embed=create_error_embed('Du kan inte varna bottar!'),
                ephemeral=True
            )
            return
        
        async with async_session() as session:
            try:
                # Skapa varning
                warning = PlayerWarning(
                    user_id=user.id,
                    guild_id=interaction.guild_id,
                    reason=reason,
                    issued_by=interaction.user.id
                )
                session.add(warning)
                await session.commit()
                
                # Räkna totala varningar
                warnings_count = await session.execute(
                    select(PlayerWarning).where(
                        PlayerWarning.user_id == user.id,
                        PlayerWarning.guild_id == interaction.guild_id,
                        PlayerWarning.active == True
                    )
                )
                total_warnings = len(warnings_count.scalars().all())
                
                # Kolla auto-ban
                auto_banned = await self.check_auto_ban(user.id, interaction.guild_id)
                
                # Uppdatera embed
                await self.update_moderation_embed(interaction.guild_id)
                
                embed = discord.Embed(
                    title="⚠️ Varning Utfärdad",
                    description=f"{user.mention} har fått en varning",
                    color=discord.Color.orange()
                )
                
                embed.add_field(
                    name="Anledning",
                    value=reason,
                    inline=False
                )
                
                embed.add_field(
                    name="Totala Varningar",
                    value=f"{total_warnings}/3",
                    inline=True
                )
                
                if auto_banned:
                    embed.add_field(
                        name="🚫 Automatisk Avstängning",
                        value="Spelaren har fått 3 varningar och är nu avstängd för 2 turneringar!",
                        inline=False
                    )
                    embed.color = discord.Color.red()
                
                await interaction.response.send_message(embed=embed)
                
                # Meddela användaren
                try:
                    dm_embed = discord.Embed(
                        title="⚠️ Du har fått en varning",
                        description=f"**Server:** {interaction.guild.name}\n**Anledning:** {reason}",
                        color=discord.Color.orange()
                    )
                    dm_embed.add_field(
                        name="Varningar",
                        value=f"{total_warnings}/3",
                        inline=False
                    )
                    if auto_banned:
                        dm_embed.add_field(
                            name="🚫 Avstängd",
                            value="Du har fått 3 varningar och är nu avstängd för 2 turneringar.",
                            inline=False
                        )
                    await user.send(embed=dm_embed)
                except:
                    pass
                
                logger.info(f'{interaction.user.name} varnade {user.name}: {reason}')
                
            except Exception as e:
                logger.error(f'Fel vid varning: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte varna spelare: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="ban-player", description="[ADMIN] Stäng av en spelare")
    @app_commands.describe(
        user="Spelaren att stänga av",
        reason="Anledning för avstängningen",
        ban_type="Typ av avstängning",
        duration="Antal turneringar (för tournament) eller timmar (för time-based)"
    )
    @is_tournament_admin()
    async def ban_player(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        reason: str,
        ban_type: Literal['temporary', 'permanent'],
        duration: Optional[int] = 2
    ):
        """Stäng av en spelare"""
        
        if user.bot:
            await interaction.response.send_message(
                embed=create_error_embed('Du kan inte stänga av bottar!'),
                ephemeral=True
            )
            return
        
        async with async_session() as session:
            try:
                # Kolla om redan bannad
                existing_ban = await session.execute(
                    select(PlayerBan).where(
                        PlayerBan.user_id == user.id,
                        PlayerBan.guild_id == interaction.guild_id,
                        PlayerBan.active == True
                    )
                )
                
                if existing_ban.scalar_one_or_none():
                    await interaction.response.send_message(
                        embed=create_error_embed('Spelaren är redan avstängd!'),
                        ephemeral=True
                    )
                    return
                
                # Skapa ban
                ban = PlayerBan(
                    user_id=user.id,
                    guild_id=interaction.guild_id,
                    reason=reason,
                    issued_by=interaction.user.id,
                    ban_type=ban_type
                )
                
                if ban_type == 'temporary':
                    ban.tournaments_banned = duration
                    ban.tournaments_served = 0
                
                session.add(ban)
                
                # Deaktivera alla varningar
                warnings = await session.execute(
                    select(PlayerWarning).where(
                        PlayerWarning.user_id == user.id,
                        PlayerWarning.guild_id == interaction.guild_id,
                        PlayerWarning.active == True
                    )
                )
                for warning in warnings.scalars().all():
                    warning.active = False
                
                await session.commit()
                
                # Uppdatera embed
                await self.update_moderation_embed(interaction.guild_id)
                
                duration_text = f"{duration} turneringar" if ban_type == 'temporary' else "Permanent"
                
                embed = discord.Embed(
                    title="🚫 Spelare Avstängd",
                    description=f"{user.mention} har stängts av",
                    color=discord.Color.red()
                )
                
                embed.add_field(
                    name="Anledning",
                    value=reason,
                    inline=False
                )
                
                embed.add_field(
                    name="Längd",
                    value=duration_text,
                    inline=True
                )
                
                await interaction.response.send_message(embed=embed)
                
                # Meddela användaren
                try:
                    dm_embed = discord.Embed(
                        title="🚫 Du har stängts av",
                        description=f"**Server:** {interaction.guild.name}\n**Anledning:** {reason}",
                        color=discord.Color.red()
                    )
                    dm_embed.add_field(
                        name="Längd",
                        value=duration_text,
                        inline=False
                    )
                    await user.send(embed=dm_embed)
                except:
                    pass
                
                logger.info(f'{interaction.user.name} avstängde {user.name}: {reason} ({duration_text})')
                
            except Exception as e:
                logger.error(f'Fel vid avstängning: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte stänga av spelare: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="unban-player", description="[ADMIN] Ta bort avstängning")
    @app_commands.describe(user="Spelaren att ta bort avstängning för")
    @is_tournament_admin()
    async def unban_player(
        self,
        interaction: discord.Interaction,
        user: discord.User
    ):
        """Ta bort avstängning"""
        
        async with async_session() as session:
            try:
                ban = await session.execute(
                    select(PlayerBan).where(
                        PlayerBan.user_id == user.id,
                        PlayerBan.guild_id == interaction.guild_id,
                        PlayerBan.active == True
                    )
                )
                ban = ban.scalar_one_or_none()
                
                if not ban:
                    await interaction.response.send_message(
                        embed=create_error_embed('Spelaren är inte avstängd!'),
                        ephemeral=True
                    )
                    return
                
                ban.active = False
                await session.commit()
                
                # Uppdatera embed
                await self.update_moderation_embed(interaction.guild_id)
                
                await interaction.response.send_message(
                    embed=create_success_embed(f'Avstängning för {user.mention} har tagits bort!')
                )
                
                logger.info(f'{interaction.user.name} tog bort avstängning för {user.name}')
                
            except Exception as e:
                logger.error(f'Fel vid unban: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte ta bort avstängning: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="clear-warnings", description="[ADMIN] Rensa varningar för en spelare")
    @app_commands.describe(user="Spelaren att rensa varningar för")
    @is_tournament_admin()
    async def clear_warnings(
        self,
        interaction: discord.Interaction,
        user: discord.User
    ):
        """Rensa alla varningar för en spelare"""
        
        async with async_session() as session:
            try:
                warnings = await session.execute(
                    select(PlayerWarning).where(
                        PlayerWarning.user_id == user.id,
                        PlayerWarning.guild_id == interaction.guild_id,
                        PlayerWarning.active == True
                    )
                )
                warnings_list = warnings.scalars().all()
                
                if not warnings_list:
                    await interaction.response.send_message(
                        embed=create_error_embed('Spelaren har inga aktiva varningar!'),
                        ephemeral=True
                    )
                    return
                
                count = len(warnings_list)
                
                for warning in warnings_list:
                    warning.active = False
                
                await session.commit()
                
                # Uppdatera embed
                await self.update_moderation_embed(interaction.guild_id)
                
                await interaction.response.send_message(
                    embed=create_success_embed(f'Rensade {count} varningar för {user.mention}!')
                )
                
                logger.info(f'{interaction.user.name} rensade {count} varningar för {user.name}')
                
            except Exception as e:
                logger.error(f'Fel vid rensning av varningar: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte rensa varningar: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="moderation-info", description="[ADMIN] Visa moderation info för en spelare")
    @app_commands.describe(user="Spelaren att visa info för")
    @is_tournament_admin()
    async def moderation_info(
        self,
        interaction: discord.Interaction,
        user: discord.User
    ):
        """Visa moderation info för en spelare"""
        
        async with async_session() as session:
            try:
                # Hämta varningar
                warnings = await session.execute(
                    select(PlayerWarning).where(
                        PlayerWarning.user_id == user.id,
                        PlayerWarning.guild_id == interaction.guild_id,
                        PlayerWarning.active == True
                    ).order_by(desc(PlayerWarning.issued_at))
                )
                warnings_list = warnings.scalars().all()
                
                # Hämta bans
                bans = await session.execute(
                    select(PlayerBan).where(
                        PlayerBan.user_id == user.id,
                        PlayerBan.guild_id == interaction.guild_id,
                        PlayerBan.active == True
                    ).order_by(desc(PlayerBan.issued_at))
                )
                bans_list = bans.scalars().all()
                
                embed = discord.Embed(
                    title=f"🛡️ Moderation Info - {user.name}",
                    color=discord.Color.blue()
                )
                
                # Varningar
                if warnings_list:
                    warnings_text = ""
                    for warning in warnings_list[:5]:
                        warnings_text += (
                            f"**<t:{int(warning.issued_at.timestamp())}:d>**\n"
                            f"{warning.reason}\n"
                            f"Av: <@{warning.issued_by}>\n\n"
                        )
                    
                    embed.add_field(
                        name=f"⚠️ Aktiva Varningar ({len(warnings_list)})",
                        value=warnings_text,
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="⚠️ Aktiva Varningar (0)",
                        value="*Inga varningar*",
                        inline=False
                    )
                
                # Bans
                if bans_list:
                    bans_text = ""
                    for ban in bans_list:
                        ban_info = ""
                        if ban.ban_type == 'temporary':
                            remaining = ban.tournaments_banned - ban.tournaments_served
                            ban_info = f"({remaining} turneringar kvar)"
                        elif ban.expires_at:
                            ban_info = f"(slutar <t:{int(ban.expires_at.timestamp())}:R>)"
                        else:
                            ban_info = "(permanent)"
                        
                        bans_text += (
                            f"**<t:{int(ban.issued_at.timestamp())}:d>** {ban_info}\n"
                            f"{ban.reason}\n"
                            f"Av: <@{ban.issued_by}>\n\n"
                        )
                    
                    embed.add_field(
                        name=f"🚫 Aktiva Avstängningar ({len(bans_list)})",
                        value=bans_text,
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="🚫 Aktiva Avstängningar (0)",
                        value="*Inga avstängningar*",
                        inline=False
                    )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            except Exception as e:
                logger.error(f'Fel vid hämtning av moderation info: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte hämta moderation info: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="set-moderation-channel", description="[ADMIN] Sätt moderation log kanal")
    @app_commands.describe(channel="Text-kanalen för moderation logs")
    @is_tournament_admin()
    async def set_moderation_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):
        """Sätt moderation log kanal"""
        
        async with async_session() as session:
            try:
                guild = await session.get(Guild, interaction.guild_id)
                
                if not guild:
                    guild = Guild(guild_id=interaction.guild_id)
                    session.add(guild)
                
                guild.moderation_channel_id = channel.id
                await session.commit()
                
                # Skapa initial embed
                await self.update_moderation_embed(interaction.guild_id)
                
                await interaction.response.send_message(
                    embed=create_success_embed(
                        f'✅ Moderation log kanal satt till {channel.mention}!'
                    ),
                    ephemeral=True
                )
                
                logger.info(f'Moderation channel satt till {channel.name} för guild {interaction.guild_id}')
                
            except Exception as e:
                logger.error(f'Fel vid setting av moderation channel: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte sätta moderation channel: {str(e)}'),
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))