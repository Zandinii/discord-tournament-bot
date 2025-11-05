import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime
from database.database import async_session
from database.models import Match, Tournament, MatchStatus
from utils.embeds import create_error_embed, create_success_embed
from sqlalchemy import select, or_
import asyncio
import logging

logger = logging.getLogger('TournamentBot.Voice')

class VoiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Lyssna på voice state changes för auto-moving"""
        
        # Om användare gick med i en channel
        if after.channel and after.channel != before.channel:
            async with async_session() as session:
                try:
                    from database.models import Guild
                    
                    # Kolla om det är lobby channel
                    guild_config = await session.get(Guild, member.guild.id)
                    if not guild_config or not guild_config.lobby_voice_channel_id:
                        return
                    
                    if after.channel.id != guild_config.lobby_voice_channel_id:
                        return
                    
                    # Användare gick med i lobby, kolla om de har en aktiv match
                    result = await session.execute(
                        select(Match).where(
                            or_(
                                Match.participant1_id == member.id,
                                Match.participant2_id == member.id
                            ),
                            Match.status == MatchStatus.ONGOING,
                            or_(
                                Match.voice_channel_1_id.isnot(None),
                                Match.voice_channel_2_id.isnot(None)
                            )
                        )
                    )
                    match = result.scalar_one_or_none()
                    
                    if not match:
                        return
                    
                    # Flytta till rätt channel
                    if match.participant1_id == member.id and match.voice_channel_1_id:
                        target_channel = member.guild.get_channel(match.voice_channel_1_id)
                    elif match.participant2_id == member.id and match.voice_channel_2_id:
                        target_channel = member.guild.get_channel(match.voice_channel_2_id)
                    else:
                        return
                    
                    if target_channel:
                        await asyncio.sleep(1)  # Kort delay
                        await member.move_to(target_channel)
                        logger.info(f'Auto-flyttade {member.name} till match channel')
                
                except Exception as e:
                    logger.error(f'Fel vid auto-move: {e}', exc_info=True)
    
    async def create_match_channels(self, guild: discord.Guild, match: Match, tournament: Tournament) -> tuple[Optional[discord.VoiceChannel], Optional[discord.VoiceChannel]]:
        """
        Skapa temporära voice channels för en match.
        
        Returns:
            Tuple med (team1_channel, team2_channel)
        """
        try:
            # Skapa kategori om den inte finns
            category_name = f"🎮 {tournament.name}"
            category = discord.utils.get(guild.categories, name=category_name)
            
            if not category:
                category = await guild.create_category(
                    name=category_name,
                    reason=f"Turnering: {tournament.name}"
                )
                logger.info(f'Skapade kategori: {category_name}')
            
            # Skapa voice channels för båda lagen
            team1_channel = await guild.create_voice_channel(
                name=f"🔵 Match {match.match_number} - Team 1",
                category=category,
                reason=f"Match {match.id}"
            )
            
            team2_channel = await guild.create_voice_channel(
                name=f"🔴 Match {match.match_number} - Team 2",
                category=category,
                reason=f"Match {match.id}"
            )
            
            logger.info(f'Skapade voice channels för match {match.id}')
            
            return team1_channel, team2_channel
            
        except discord.Forbidden:
            logger.error('Bot saknar permissions för att skapa voice channels!')
            return None, None
        except Exception as e:
            logger.error(f'Fel vid skapande av voice channels: {e}', exc_info=True)
            return None, None
    
    async def move_players_to_channels(
        self, 
        guild: discord.Guild, 
        match: Match,
        team1_channel: discord.VoiceChannel,
        team2_channel: discord.VoiceChannel
    ) -> tuple[int, int]:
        """
        Flytta spelare till deras respektive voice channels.
        
        Returns:
            Tuple med (antal flyttade till team1, antal flyttade till team2)
        """
        moved_team1 = 0
        moved_team2 = 0
        
        try:
            # Hämta members
            participant1 = guild.get_member(match.participant1_id)
            participant2 = guild.get_member(match.participant2_id)
            
            # Flytta participant 1 till team1 channel
            if participant1 and participant1.voice:
                try:
                    await participant1.move_to(team1_channel)
                    moved_team1 += 1
                    logger.info(f'Flyttade {participant1.name} till team1 channel')
                except discord.HTTPException as e:
                    logger.warning(f'Kunde inte flytta {participant1.name}: {e}')
            
            # Flytta participant 2 till team2 channel
            if participant2 and participant2.voice:
                try:
                    await participant2.move_to(team2_channel)
                    moved_team2 += 1
                    logger.info(f'Flyttade {participant2.name} till team2 channel')
                except discord.HTTPException as e:
                    logger.warning(f'Kunde inte flytta {participant2.name}: {e}')
            
            return moved_team1, moved_team2
            
        except Exception as e:
            logger.error(f'Fel vid flyttning av spelare: {e}', exc_info=True)
            return moved_team1, moved_team2
    
    async def cleanup_match_channels(
        self, 
        guild: discord.Guild, 
        match: Match,
        lobby_channel_id: Optional[int] = None
    ):
        """
        Ta bort match voice channels och flytta spelare tillbaka till lobby.
        """
        try:
            channels_to_delete = []
            members_to_move = []
            
            # Hämta channels
            if match.voice_channel_1_id:
                channel1 = guild.get_channel(match.voice_channel_1_id)
                if channel1:
                    # Samla medlemmar innan vi tar bort kanalen
                    members_to_move.extend(channel1.members)
                    channels_to_delete.append(channel1)
            
            if match.voice_channel_2_id:
                channel2 = guild.get_channel(match.voice_channel_2_id)
                if channel2:
                    members_to_move.extend(channel2.members)
                    channels_to_delete.append(channel2)
            
            # Flytta spelare tillbaka till lobby (om lobby finns)
            if lobby_channel_id:
                lobby = guild.get_channel(lobby_channel_id)
                if lobby and isinstance(lobby, discord.VoiceChannel):
                    for member in members_to_move:
                        try:
                            await member.move_to(lobby)
                            logger.info(f'Flyttade {member.name} tillbaka till lobby')
                        except discord.HTTPException as e:
                            logger.warning(f'Kunde inte flytta {member.name} till lobby: {e}')
            
            # Vänta lite innan vi tar bort kanalerna
            await asyncio.sleep(2)
            
            # Ta bort channels
            for channel in channels_to_delete:
                try:
                    await channel.delete(reason=f"Match {match.id} avslutad")
                    logger.info(f'Tog bort voice channel: {channel.name}')
                except discord.HTTPException as e:
                    logger.warning(f'Kunde inte ta bort channel {channel.name}: {e}')
            
        except Exception as e:
            logger.error(f'Fel vid cleanup av channels: {e}', exc_info=True)
    
    @app_commands.command(name="setup-match", description="[ADMIN] Skapa voice channels för en match")
    @app_commands.describe(match_id="Match-ID")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_match(self, interaction: discord.Interaction, match_id: int):
        """Manuellt skapa voice channels för en match"""
        
        async with async_session() as session:
            try:
                match = await session.get(Match, match_id)
                
                if not match:
                    await interaction.response.send_message(
                        embed=create_error_embed('Matchen hittades inte!'),
                        ephemeral=True
                    )
                    return
                
                tournament = await session.get(Tournament, match.tournament_id)
                
                if not tournament:
                    await interaction.response.send_message(
                        embed=create_error_embed('Turneringen hittades inte!'),
                        ephemeral=True
                    )
                    return
                
                # Skapa channels
                await interaction.response.defer(ephemeral=True)
                
                team1_channel, team2_channel = await self.create_match_channels(
                    interaction.guild,
                    match,
                    tournament
                )
                
                if not team1_channel or not team2_channel:
                    await interaction.followup.send(
                        embed=create_error_embed('Kunde inte skapa voice channels! Kolla bot permissions.'),
                        ephemeral=True
                    )
                    return
                
                # Spara channel IDs
                match.voice_channel_1_id = team1_channel.id
                match.voice_channel_2_id = team2_channel.id
                match.status = MatchStatus.ONGOING
                match.started_at = datetime.utcnow()
                await session.commit()
                
                # Flytta spelare
                moved_t1, moved_t2 = await self.move_players_to_channels(
                    interaction.guild,
                    match,
                    team1_channel,
                    team2_channel
                )
                
                embed = discord.Embed(
                    title="✅ Match Setup Klar!",
                    description=f"Voice channels skapade för **Match {match.match_number}**",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="🔵 Team 1 Channel",
                    value=team1_channel.mention,
                    inline=True
                )
                
                embed.add_field(
                    name="🔴 Team 2 Channel",
                    value=team2_channel.mention,
                    inline=True
                )
                
                embed.add_field(
                    name="👥 Spelare Flyttade",
                    value=f"Team 1: {moved_t1}\nTeam 2: {moved_t2}",
                    inline=False
                )
                
                if moved_t1 == 0 or moved_t2 == 0:
                    embed.add_field(
                        name="⚠️ Notering",
                        value="Vissa spelare var inte i en voice channel och kunde inte flyttas automatiskt.",
                        inline=False
                    )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                # Skicka notis till deltagare
                notification_channel = interaction.channel
                await notification_channel.send(
                    f"🎮 <@{match.participant1_id}> <@{match.participant2_id}>\n\n"
                    f"**Match {match.match_number}** är redo!\n"
                    f"🔵 Team 1: {team1_channel.mention}\n"
                    f"🔴 Team 2: {team2_channel.mention}\n\n"
                    f"*Använd `/report-win {match.id}` när matchen är klar!*"
                )
                
                logger.info(f'Setup match {match_id} med voice channels')
                
            except Exception as e:
                logger.error(f'Fel vid setup av match: {e}', exc_info=True)
                await interaction.followup.send(
                    embed=create_error_embed(f'Kunde inte sätta upp match: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="cleanup-match", description="[ADMIN] Ta bort voice channels för en match")
    @app_commands.describe(match_id="Match-ID")
    @app_commands.checks.has_permissions(administrator=True)
    async def cleanup_match_cmd(self, interaction: discord.Interaction, match_id: int):
        """Manuellt rensa voice channels för en match"""
        
        async with async_session() as session:
            try:
                match = await session.get(Match, match_id)
                
                if not match:
                    await interaction.response.send_message(
                        embed=create_error_embed('Matchen hittades inte!'),
                        ephemeral=True
                    )
                    return
                
                await interaction.response.defer(ephemeral=True)
                
                # Hämta guild config för lobby channel
                from database.models import Guild
                guild_config = await session.get(Guild, interaction.guild_id)
                lobby_id = guild_config.lobby_voice_channel_id if guild_config else None
                
                # Cleanup
                await self.cleanup_match_channels(interaction.guild, match, lobby_id)
                
                # Uppdatera match i databas
                match.voice_channel_1_id = None
                match.voice_channel_2_id = None
                await session.commit()
                
                await interaction.followup.send(
                    embed=create_success_embed(f'Voice channels för match {match_id} har rensats!'),
                    ephemeral=True
                )
                
                logger.info(f'Cleanup match {match_id} voice channels')
                
            except Exception as e:
                logger.error(f'Fel vid cleanup: {e}', exc_info=True)
                await interaction.followup.send(
                    embed=create_error_embed(f'Kunde inte rensa channels: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="cleanup-all", description="[ADMIN] Ta bort alla match voice channels")
    @app_commands.checks.has_permissions(administrator=True)
    async def cleanup_all(self, interaction: discord.Interaction):
        """Emergency cleanup av alla match-relaterade channels"""
        
        await interaction.response.defer(ephemeral=True)
        
        deleted_count = 0
        
        try:
            # Hitta alla kategorier som börjar med 🎮
            for category in interaction.guild.categories:
                if category.name.startswith("🎮"):
                    # Ta bort alla voice channels i kategorin
                    for channel in category.voice_channels:
                        try:
                            await channel.delete(reason="Cleanup all")
                            deleted_count += 1
                            await asyncio.sleep(0.5)  # Rate limit protection
                        except Exception as e:
                            logger.warning(f'Kunde inte ta bort {channel.name}: {e}')
                    
                    # Ta bort kategorin om den är tom
                    if len(category.channels) == 0:
                        try:
                            await category.delete(reason="Cleanup all")
                        except Exception as e:
                            logger.warning(f'Kunde inte ta bort kategori {category.name}: {e}')
            
            await interaction.followup.send(
                embed=create_success_embed(f'✅ Rensade {deleted_count} voice channels!'),
                ephemeral=True
            )
            
            logger.info(f'Cleanup all: {deleted_count} channels borttagna')
            
        except Exception as e:
            logger.error(f'Fel vid cleanup all: {e}', exc_info=True)
            await interaction.followup.send(
                embed=create_error_embed(f'Kunde inte slutföra cleanup: {str(e)}'),
                ephemeral=True
            )
    
    @app_commands.command(name="set-lobby", description="[ADMIN] Sätt lobby voice channel")
    @app_commands.describe(channel="Voice channel att använda som lobby")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_lobby(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        """Sätt lobby voice channel för servern"""
        
        async with async_session() as session:
            try:
                from database.models import Guild
                
                guild = await session.get(Guild, interaction.guild_id)
                
                if not guild:
                    guild = Guild(guild_id=interaction.guild_id)
                    session.add(guild)
                
                guild.lobby_voice_channel_id = channel.id
                await session.commit()
                
                await interaction.response.send_message(
                    embed=create_success_embed(
                        f'✅ Lobby voice channel satt till {channel.mention}!\n\n'
                        f'Spelare kommer automatiskt flyttas tillbaka hit efter matcher.'
                    ),
                    ephemeral=True
                )
                
                logger.info(f'Lobby channel satt till {channel.name} för guild {interaction.guild_id}')
                
            except Exception as e:
                logger.error(f'Fel vid setting av lobby: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte sätta lobby: {str(e)}'),
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(VoiceCog(bot))