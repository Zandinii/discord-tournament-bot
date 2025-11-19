import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime
from database.database import async_session
from database.models import (
    Tournament, TournamentParticipant, Match, Player,
    TournamentStatus, MatchStatus, ParticipantType
)
from utils.embeds import (
    create_tournament_announcement, create_bracket_embed,
    create_error_embed, create_success_embed
)
from utils.bracket import (
    generate_single_elimination, generate_round_robin,
    calculate_total_rounds, get_bracket_structure
)
from cogs.match import trigger_match_created_event
from sqlalchemy import select
import logging


logger = logging.getLogger('TournamentBot.Tournament')

async def auto_setup_matches(bot, guild_id: int, tournament_id: int):
    """Automatiskt sätt upp voice channels för första rundan"""
    try:
        from cogs.match import trigger_match_created_event
        from discord import Self
        
        guild = bot.get_guild(guild_id)
        if not guild:
            return
        
        async with async_session() as session:
            tournament = await session.get(Tournament, tournament_id)
            if not tournament:
                return
            
            # Hämta första rundan som är pending
            result = await session.execute(
                select(Match).where(
                    Match.tournament_id == tournament_id,
                    Match.round_number == 1,
                    Match.status == MatchStatus.PENDING
                )
            )
            matches = result.scalars().all()
            
            voice_cog = bot.get_cog('VoiceCog')
            if not voice_cog:
                return
            
            # Setup varje match
            for match in matches:
                team1_channel, team2_channel = await voice_cog.create_match_channels(
                    guild, match, tournament
                )
                
                if team1_channel and team2_channel:
                    match.voice_channel_1_id = team1_channel.id
                    match.voice_channel_2_id = team2_channel.id
                    match.status = MatchStatus.ONGOING
                    match.started_at = datetime.utcnow()
                    
                    # Flytta spelare om de är i voice
                    await voice_cog.move_players_to_channels(
                        guild, match, team1_channel, team2_channel
                    )

                    # Starta map ban phase
                    await voice_cog.start_map_ban_phase(
                        guild, match, tournament, team1_channel, team2_channel
                    )
            
            await session.commit()
            await trigger_match_created_event(Self.bot, match.id)
            logger.info(f'Auto-setup {len(matches)} matcher för turnering {tournament_id}')
            
    except Exception as e:
        logger.error(f'Fel vid auto-setup: {e}', exc_info=True)

async def update_lobby_bracket(bot, guild_id: int, tournament_id: int):
    """Uppdatera bracket embed i lobby voice channel text chat"""
    try:
        from database.models import Guild
        from utils.embeds import create_bracket_embed_async
        from utils.bracket import get_bracket_structure
        
        async with async_session() as session:
            # Hämta guild config för lobby channel
            guild_config = await session.get(Guild, guild_id)
            if not guild_config or not guild_config.lobby_voice_channel_id:
                logger.warning(f'Ingen lobby channel satt för guild {guild_id}')
                return
            
            guild = bot.get_guild(guild_id)
            if not guild:
                return
            
            lobby_channel = guild.get_channel(guild_config.lobby_voice_channel_id)
            if not lobby_channel:
                return
            
            # Hämta turnering och matcher
            tournament = await session.get(Tournament, tournament_id)
            if not tournament:
                return
            
            result = await session.execute(
                select(Match).where(Match.tournament_id == tournament_id)
            )
            matches = result.scalars().all()
            
            if not matches:
                return
            
            # Hitta aktuellt round
            bracket_structure = get_bracket_structure(tournament_id, matches)
            current_round = 1
            for rnd in sorted(bracket_structure.keys()):
                round_matches = bracket_structure[rnd]
                if any(m.status != MatchStatus.COMPLETED for m in round_matches):
                    current_round = rnd
                    break
            
            # Skapa bracket embed med async version (visar riktiga namn)
            embed = await create_bracket_embed_async(session, tournament, matches, current_round)
            
            # Försök hitta befintligt bracket meddelande
            bracket_message_found = False
            async for message in lobby_channel.history(limit=50):
                if message.author == bot.user and message.embeds:
                    if message.embeds[0].title and "Bracket" in message.embeds[0].title:
                        await message.edit(embed=embed)
                        bracket_message_found = True
                        logger.info(f'Uppdaterade bracket i lobby för turnering {tournament_id}')
                        break
            
            # Om inget meddelande hittades, skapa nytt
            if not bracket_message_found:
                await lobby_channel.send(embed=embed)
                logger.info(f'Skapade nytt bracket meddelande i lobby för turnering {tournament_id}')
    
    except Exception as e:
        logger.error(f'Fel vid uppdatering av lobby bracket: {e}', exc_info=True)
class TournamentCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="tournament-start", description="[ADMIN] Starta en turnering och generera bracket")
    @app_commands.describe(tournament_id="Turnerings-ID")
    @app_commands.checks.has_permissions(administrator=True)
    async def tournament_start(self, interaction: discord.Interaction, tournament_id: int):
        """Starta turnering och generera bracket"""
        
        async with async_session() as session:
            try:
                # Hämta turnering
                tournament = await session.get(Tournament, tournament_id)
                
                if not tournament:
                    await interaction.response.send_message(
                        embed=create_error_embed('Turneringen hittades inte!'),
                        ephemeral=True
                    )
                    return
                
                if tournament.guild_id != interaction.guild_id:
                    await interaction.response.send_message(
                        embed=create_error_embed('Denna turnering tillhör inte denna server!'),
                        ephemeral=True
                    )
                    return
                
                if tournament.status != TournamentStatus.SIGNUP:
                    await interaction.response.send_message(
                        embed=create_error_embed('Turneringen är redan startad eller avslutad!'),
                        ephemeral=True
                    )
                    return
                
                # Hämta deltagare
                result = await session.execute(
                    select(TournamentParticipant).where(
                        TournamentParticipant.tournament_id == tournament_id
                    )
                )
                participants = result.scalars().all()
                
                if len(participants) < 2:
                    await interaction.response.send_message(
                        embed=create_error_embed('Minst 2 deltagare krävs för att starta turneringen!'),
                        ephemeral=True
                    )
                    return
                
                # Generera bracket baserat på typ
                matches = []
                if tournament.game_type == 'single_elim':
                    matches = generate_single_elimination(tournament_id, participants)
                elif tournament.game_type == 'round_robin':
                    matches = generate_round_robin(tournament_id, participants)
                elif tournament.game_type == 'double_elim':
                    # TODO: Implementera double elimination senare
                    await interaction.response.send_message(
                        embed=create_error_embed('Double elimination är inte implementerat än!'),
                        ephemeral=True
                    )
                    return
                
                # Spara matcher i databas
                for match in matches:
                    session.add(match)
                
                # Uppdatera turnerings-status
                tournament.status = TournamentStatus.ONGOING
                
                # Uppdatera deltagares tournament participation count
                for participant in participants:
                    player = await session.get(Player, participant.participant_id)
                    if player:
                        player.tournaments_participated += 1
                
                await session.commit()
                
                 # Auto-setup första rundan (lägg till denna)
                await auto_setup_matches(
                    self.bot,
                    interaction.guild_id,
                    tournament_id
                )

                # Skapa initial bracket i lobby
                await update_lobby_bracket(
                    self.bot,
                    interaction.guild_id,
                    tournament_id
                )

                # Skapa bracket embed
                embed = discord.Embed(
                    title=f"🏆 {tournament.name} - Turnering Startad!",
                    description=f"Bracket har genererats med **{len(participants)} deltagare**!",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                
                # Visa första rundan
                round_1_matches = [m for m in matches if m.round_number == 1 and m.status == MatchStatus.PENDING]
                
                if round_1_matches:
                    matches_text = ""
                    for match in round_1_matches[:10]:  # Max 10
                        p1_name = f"Deltagare {match.participant1_id}" if match.participant1_id else "BYE"
                        p2_name = f"Deltagare {match.participant2_id}" if match.participant2_id else "BYE"
                        matches_text += f"**Match {match.match_number}:** {p1_name} vs {p2_name}\n"
                    
                    embed.add_field(
                        name="📋 Round 1 Matcher",
                        value=matches_text,
                        inline=False
                    )
                
                total_rounds = calculate_total_rounds(len(participants), tournament.game_type)
                embed.add_field(
                    name="ℹ️ Information",
                    value=f"**Totala Rounds:** {total_rounds}\n"
                          f"**Turneringstyp:** {tournament.game_type.replace('_', ' ').title()}\n"
                          f"**Mode:** {tournament.game_mode}",
                    inline=False
                )
                
                embed.set_footer(text=f"Använd /bracket {tournament_id} för att se hela bracketen")
                
                await interaction.response.send_message(embed=embed)
                
                logger.info(f'Turnering {tournament_id} startad av {interaction.user.name} med {len(participants)} deltagare')
                
            except Exception as e:
                logger.error(f'Fel vid start av turnering: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte starta turnering: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="bracket", description="Visa turnerings-bracket")
    @app_commands.describe(
        tournament_id="Turnerings-ID",
        round_number="Vilket round att visa (standard: nuvarande)"
    )
    async def bracket(
        self, 
        interaction: discord.Interaction, 
        tournament_id: int,
        round_number: Optional[int] = None
    ):
        """Visa turnerings-bracket"""
        
        async with async_session() as session:
            try:
                # Hämta turnering
                tournament = await session.get(Tournament, tournament_id)
                
                if not tournament:
                    await interaction.response.send_message(
                        embed=create_error_embed('Turneringen hittades inte!'),
                        ephemeral=True
                    )
                    return
                
                # Hämta alla matcher
                result = await session.execute(
                    select(Match).where(Match.tournament_id == tournament_id)
                )
                matches = result.scalars().all()
                
                if not matches:
                    await interaction.response.send_message(
                        embed=create_error_embed('Inga matcher hittades! Turneringen kanske inte har startat än.'),
                        ephemeral=True
                    )
                    return
                
                # Bestäm vilket round att visa
                if round_number is None:
                    # Hitta första round som inte är helt klar
                    bracket_structure = get_bracket_structure(tournament_id, matches)
                    current_round = 1
                    for rnd in sorted(bracket_structure.keys()):
                        round_matches = bracket_structure[rnd]
                        if any(m.status != MatchStatus.COMPLETED for m in round_matches):
                            current_round = rnd
                            break
                    round_number = current_round
                
                # Skapa embed
                embed = create_bracket_embed(tournament, matches, round_number)
                
                await interaction.response.send_message(embed=embed)
                
            except Exception as e:
                logger.error(f'Fel vid visning av bracket: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte visa bracket: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="tournament-cancel", description="[ADMIN] Avbryt en turnering")
    @app_commands.describe(tournament_id="Turnerings-ID")
    @app_commands.checks.has_permissions(administrator=True)
    async def tournament_cancel(self, interaction: discord.Interaction, tournament_id: int):
        """Avbryt en turnering"""
        
        async with async_session() as session:
            try:
                tournament = await session.get(Tournament, tournament_id)
                
                if not tournament:
                    await interaction.response.send_message(
                        embed=create_error_embed('Turneringen hittades inte!'),
                        ephemeral=True
                    )
                    return
                
                if tournament.guild_id != interaction.guild_id:
                    await interaction.response.send_message(
                        embed=create_error_embed('Denna turnering tillhör inte denna server!'),
                        ephemeral=True
                    )
                    return
                
                if tournament.status == TournamentStatus.COMPLETED:
                    await interaction.response.send_message(
                        embed=create_error_embed('Turneringen är redan avslutad!'),
                        ephemeral=True
                    )
                    return
                
                tournament.status = TournamentStatus.CANCELLED
                await session.commit()
                
                await interaction.response.send_message(
                    embed=create_success_embed(f'Turnering **{tournament.name}** har avbrutits!'),
                    ephemeral=True
                )
                
                logger.info(f'Turnering {tournament_id} avbruten av {interaction.user.name}')
                
            except Exception as e:
                logger.error(f'Fel vid avbrytning av turnering: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte avbryta turnering: {str(e)}'),
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(TournamentCog(bot))