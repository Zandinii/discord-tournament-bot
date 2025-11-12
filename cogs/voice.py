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
        Skapa temporära voice channels för en match med rätt namn.
        
        Returns:
            Tuple med (team1_channel, team2_channel)
        """
        try:
            from database.models import Team, Player, ParticipantType
            
            # Skapa kategori om den inte finns
            category_name = f"🎮 {tournament.name}"
            category = discord.utils.get(guild.categories, name=category_name)
            
            if not category:
                category = await guild.create_category(
                    name=category_name,
                    reason=f"Turnering: {tournament.name}"
                )
                logger.info(f'Skapade kategori: {category_name}')
            
            # Bestäm namn för voice channels baserat på deltagare
            is_team_tournament = tournament.game_mode in ['2v2', '5v5']
            
            async with async_session() as session:
                if is_team_tournament:
                    # Team turnering - använd lagnamn
                    team1 = await session.get(Team, match.participant1_id)
                    team2 = await session.get(Team, match.participant2_id)
                    
                    team1_name = team1.name if team1 else f"Team {match.participant1_id}"
                    team2_name = team2.name if team2 else f"Team {match.participant2_id}"
                    
                    # Lägg till tag om det finns
                    if team1 and team1.tag:
                        team1_name = f"[{team1.tag}] {team1.name}"
                    if team2 and team2.tag:
                        team2_name = f"[{team2.tag}] {team2.name}"
                else:
                    # 1v1 - använd spelarnamn
                    player1 = await session.get(Player, match.participant1_id)
                    player2 = await session.get(Player, match.participant2_id)
                    
                    team1_name = player1.username if player1 else f"Spelare {match.participant1_id}"
                    team2_name = player2.username if player2 else f"Spelare {match.participant2_id}"
            
            # Begränsa längd på namn (Discord max 100 tecken för channel namn)
            team1_name = team1_name[:50] if len(team1_name) > 50 else team1_name
            team2_name = team2_name[:50] if len(team2_name) > 50 else team2_name
            
            # Skapa voice channels med rätt namn
            team1_channel = await guild.create_voice_channel(
                name=f"🔵 {team1_name}",
                category=category,
                reason=f"Match {match.id} - Round {match.round_number}"
            )
            
            team2_channel = await guild.create_voice_channel(
                name=f"🔴 {team2_name}",
                category=category,
                reason=f"Match {match.id} - Round {match.round_number}"
            )
            
            logger.info(f'Skapade voice channels för match {match.id}: "{team1_name}" vs "{team2_name}"')
            
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
        
    async def start_map_ban_phase(
        self,
        guild: discord.Guild,
        match: Match,
        tournament: Tournament,
        team1_channel: discord.VoiceChannel,
        team2_channel: discord.VoiceChannel
    ):
        """
        Starta map ban-fasen för en match i voice channel text chat.
        """
        try:
            # Kolla om map pool finns
            if not tournament.map_pool:
                logger.info(f'Ingen map pool för turnering {tournament.id}, skippar ban phase')
                return
            
            # Parse map pool
            try:
                maps = [m.strip() for m in tournament.map_pool.split(',')]
            except:
                logger.warning(f'Kunde inte parse map pool för turnering {tournament.id}')
                return
            
            if len(maps) < 2:
                logger.info(f'För få kartor i poolen för ban phase')
                return
            
            # Bestäm vilket round vi är i (groupstage vs playoffs)
            bo_format = tournament.bo_format_groupstage if match.round_number <= 2 else tournament.bo_format_playoffs
            
            # Beräkna antal bans som behövs
            maps_needed = bo_format  # 1 för BO1, 3 för BO3
            total_bans = len(maps) - maps_needed
            
            if total_bans <= 0:
                logger.info(f'Inte tillräckligt med kartor för ban phase')
                return
            
            # Använd voice channel text chats direkt!
            # Discord voice channels har automatiskt text chat
            
            # Skapa ban view och embeds
            from cogs.match import MapBanView
            
            view = MapBanView(
                match_id=match.id,
                tournament=tournament,
                available_maps=maps,
                total_bans_needed=total_bans,
                maps_to_keep=maps_needed,
                participant1_id=match.participant1_id,
                participant2_id=match.participant2_id,
                bot=self.bot
            )
            
            # Skapa initial embed
            embed = discord.Embed(
                title=f"🗺️ Map Ban Phase",
                description=f"**Match ID: `{match.id}`**\n**Best of {bo_format}**\n\n"
                        f"Lagkaptener, banna {total_bans} kartor!\n"
                        f"Ni har 30 sekunder per ban.",
                color=0xFF9900,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="📋 Tillgängliga Kartor",
                value="\n".join([f"✅ {m}" for m in maps]),
                inline=False
            )
            
            embed.add_field(
                name="🚫 Bannade Kartor",
                value="*Inga bans än*",
                inline=False
            )
            
            embed.set_footer(text=f"Match ID: {match.id}")
            
            # Skicka SAMMA meddelande till båda voice channels text chat
            # (Voice channels har automatisk text chat som är synlig för alla i kanalen)
            msg1 = await team1_channel.send(
                content=f"<@{match.participant1_id}> <@{match.participant2_id}>",
                embed=embed,
                view=view
            )
            msg2 = await team2_channel.send(
                content=f"<@{match.participant1_id}> <@{match.participant2_id}>",
                embed=embed,
                view=view
            )
            
            # Spara message IDs
            async with async_session() as session:
                match_db = await session.get(Match, match.id)
                match_db.ban_message_id_team1 = msg1.id
                match_db.ban_message_id_team2 = msg2.id
                await session.commit()
            
            # Sätt upp view references
            view.team1_voice_channel = team1_channel
            view.team2_voice_channel = team2_channel
            view.message1 = msg1
            view.message2 = msg2
            
            # Starta timeout timer
            view.ban_timer_task = asyncio.create_task(view.ban_timeout())
            
            logger.info(f'Startade map ban phase för match {match.id} i voice channel text chats')
            
        except Exception as e:
            logger.error(f'Fel vid start av map ban phase: {e}', exc_info=True)
        
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

                # Starta map ban phase
                await self.start_map_ban_phase(
                    interaction.guild,
                    match,
                    tournament,
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