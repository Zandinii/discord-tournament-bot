import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime
from database.database import async_session
from database.models import (
    Match, Tournament, Player, TournamentParticipant,
    MatchStatus, TournamentStatus, ParticipantType, ChampionHistory,
    MatchHistory
)
from utils.embeds import (
    create_match_embed, create_error_embed, create_success_embed
)
from utils.elo import calculate_elo, elo_change_description
from utils.bracket import advance_winner, get_tournament_winner
from sqlalchemy import select, and_, or_
import logging
import random
import asyncio

logger = logging.getLogger('TournamentBot.Match')

class MapBanView(discord.ui.View):
    """View för map bans med knappar"""
    
    def __init__(
        self, 
        match_id: int, 
        tournament,
        available_maps: list[str],
        total_bans_needed: int,
        maps_to_keep: int,
        participant1_id: int,
        participant2_id: int,
        bot
    ):
        super().__init__(timeout=None)
        self.match_id = match_id
        self.tournament = tournament
        self.available_maps = available_maps.copy()
        self.banned_maps = []
        self.total_bans_needed = total_bans_needed
        self.maps_to_keep = maps_to_keep
        self.participant1_id = participant1_id
        self.participant2_id = participant2_id
        self.current_banner = participant1_id  # Börja med team 1
        self.bans_done = 0
        self.bot = bot
        self.team1_voice_channel = None  # Voice channel (har text chat)
        self.team2_voice_channel = None  # Voice channel (har text chat)
        self.message1 = None
        self.message2 = None
        self.ban_timer_task = None
        
        # Skapa knappar för varje karta
        self.create_buttons()
    
    def create_buttons(self):
        """Skapa knappar för alla kartor"""
        self.clear_items()
        
        for map_name in self.available_maps:
            button = discord.ui.Button(
                label=map_name,
                style=discord.ButtonStyle.primary,
                custom_id=f"ban_{map_name}"
            )
            button.callback = self.create_ban_callback(map_name)
            self.add_item(button)
    
    def create_ban_callback(self, map_name: str):
        """Skapa callback för en specifik karta"""
        async def callback(interaction: discord.Interaction):
            await self.handle_ban(interaction, map_name)
        return callback
    
    async def handle_ban(self, interaction: discord.Interaction, map_name: str):
        """Hantera när någon bannar en karta"""
        
        # Kolla om det är rätt person som bannar
        is_team_tournament = self.tournament.game_mode in ['2v2', '5v5']
        
        if is_team_tournament:
            # Kolla om användaren är captain för det lag som ska banna
            from database.models import Team
            async with async_session() as session:
                if self.current_banner == self.participant1_id:
                    team = await session.get(Team, self.participant1_id)
                    if not team or team.captain_id != interaction.user.id:
                        await interaction.response.send_message(
                            "❌ Endast lagkapten kan banna!", ephemeral=True
                        )
                        return
                else:
                    team = await session.get(Team, self.participant2_id)
                    if not team or team.captain_id != interaction.user.id:
                        await interaction.response.send_message(
                            "❌ Endast lagkapten kan banna!", ephemeral=True
                        )
                        return
        else:
            # 1v1, kolla om det är rätt spelare
            if interaction.user.id != self.current_banner:
                await interaction.response.send_message(
                    "❌ Det är inte din tur att banna!", ephemeral=True
                )
                return
        
        # Banna kartan
        if map_name not in self.available_maps:
            await interaction.response.send_message(
                "❌ Denna karta är redan bannad!", ephemeral=True
            )
            return
        
        # Spara ban i databas
        from database.models import MapBan
        async with async_session() as session:
            map_ban = MapBan(
                match_id=self.match_id,
                participant_id=self.current_banner,
                map_name=map_name,
                ban_order=self.bans_done + 1
            )
            session.add(map_ban)
            await session.commit()
        
        # Ta bort från tillgängliga
        self.available_maps.remove(map_name)
        self.banned_maps.append({
            'map': map_name,
            'banned_by': self.current_banner,
            'order': self.bans_done + 1
        })
        self.bans_done += 1
        
        await interaction.response.defer()
        
        # Uppdatera embeds
        await self.update_embeds()
        
        # Kolla om vi är klara
        if self.bans_done >= self.total_bans_needed:
            await self.finish_ban_phase()
        else:
            # Byt vems tur det är
            self.current_banner = self.participant2_id if self.current_banner == self.participant1_id else self.participant1_id
            
            # Starta timer för nästa ban
            if self.ban_timer_task:
                self.ban_timer_task.cancel()
            self.ban_timer_task = asyncio.create_task(self.ban_timeout())
    
    async def update_embeds(self):
        """Uppdatera båda embed-meddelandena"""
        
        from utils.embeds import create_map_ban_embed
        
        embed = create_map_ban_embed(
            match_id=self.match_id,
            bo_format=self.maps_to_keep,
            available_maps=self.available_maps,
            banned_maps=self.banned_maps,
            current_banner_id=self.current_banner,
            bans_done=self.bans_done,
            total_bans=self.total_bans_needed
        )
        
        # Uppdatera knappar
        self.create_buttons()
        
        # Uppdatera båda meddelanden i voice channel text chats
        try:
            if self.message1:
                await self.message1.edit(embed=embed, view=self)
            if self.message2:
                await self.message2.edit(embed=embed, view=self)
        except Exception as e:
            logger.error(f'Fel vid uppdatering av embeds: {e}')
    
    async def ban_timeout(self):
        """Hantera timeout (30 sekunder)"""
        try:
            await asyncio.sleep(30)
            
            # Om vi fortfarande väntar på ban, välj random
            if self.bans_done < self.total_bans_needed and self.available_maps:
                random_map = random.choice(self.available_maps)
                
                # Spara ban
                from database.models import MapBan
                async with async_session() as session:
                    map_ban = MapBan(
                        match_id=self.match_id,
                        participant_id=self.current_banner,
                        map_name=random_map,
                        ban_order=self.bans_done + 1
                    )
                    session.add(map_ban)
                    await session.commit()
                
                # Ta bort från tillgängliga
                self.available_maps.remove(random_map)
                self.banned_maps.append({
                    'map': random_map,
                    'banned_by': self.current_banner,
                    'order': self.bans_done + 1
                })
                self.bans_done += 1
                
                # Notifiera timeout i båda voice channel text chats
                if self.team1_voice_channel:
                    await self.team1_voice_channel.send(
                        f"⏰ <@{self.current_banner}> fick timeout! **{random_map}** bannades automatiskt."
                    )
                if self.team2_voice_channel:
                    await self.team2_voice_channel.send(
                        f"⏰ <@{self.current_banner}> fick timeout! **{random_map}** bannades automatiskt."
                    )
                
                # Uppdatera embeds
                await self.update_embeds()
                
                # Kolla om vi är klara
                if self.bans_done >= self.total_bans_needed:
                    await self.finish_ban_phase()
                else:
                    # Byt tur
                    self.current_banner = self.participant2_id if self.current_banner == self.participant1_id else self.participant1_id
                    self.ban_timer_task = asyncio.create_task(self.ban_timeout())
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f'Fel i ban timeout: {e}', exc_info=True)
    
    async def finish_ban_phase(self):
        """Avsluta ban phase och slumpa kartor + sidor"""
        
        # Disable alla knappar
        for item in self.children:
            item.disabled = True
        
        try:
            await self.message1.edit(view=self)
            await self.message2.edit(view=self)
        except:
            pass
        
        # Slumpa ordning på kvarvarande kartor
        random.shuffle(self.available_maps)
        
        # Skapa map list med sidor
        maps_to_play = []
        sides = ['CT', 'T']  # För CS2
        
        for map_name in self.available_maps[:self.maps_to_keep]:
            # Slumpa vilken sida participant1 börjar på
            p1_side = random.choice(sides)
            p2_side = 'T' if p1_side == 'CT' else 'CT'
            
            maps_to_play.append({
                'map': map_name,
                'side_p1': p1_side,
                'side_p2': p2_side
            })
        
        # Spara i databas
        import json
        async with async_session() as session:
            match = await session.get(Match, self.match_id)
            match.maps_to_play = json.dumps(maps_to_play)
            match.ban_phase_complete = True
            await session.commit()
        
        # Skapa final embed
        from utils.embeds import create_map_ban_complete_embed
        
        final_embed = create_map_ban_complete_embed(
            match_id=self.match_id,
            bo_format=self.maps_to_keep,
            maps_to_play=maps_to_play,
            participant1_id=self.participant1_id,
            participant2_id=self.participant2_id
        )
        
        # Skicka till båda voice channel text chats
        if self.team1_voice_channel:
            await self.team1_voice_channel.send(embed=final_embed)
        if self.team2_voice_channel:
            await self.team2_voice_channel.send(embed=final_embed)
        
        logger.info(f'Map ban phase klar för match {self.match_id}')

async def cleanup_voice_after_match(bot, guild_id: int, match_id: int):
    """Helper funktion för att rensa voice channels efter match"""
    try:
        guild = bot.get_guild(guild_id)
        if not guild:
            return
        
        async with async_session() as session:
            match = await session.get(Match, match_id)
            if not match:
                return
            
            from database.models import Guild
            guild_config = await session.get(Guild, guild_id)
            lobby_id = guild_config.lobby_voice_channel_id if guild_config else None
            
            # Använd voice cog för cleanup
            voice_cog = bot.get_cog('VoiceCog')
            if voice_cog:
                await voice_cog.cleanup_match_channels(guild, match, lobby_id)
    except Exception as e:
        logger.error(f'Fel vid voice cleanup efter match: {e}')

class MatchResultView(discord.ui.View):
    """View för att bekräfta match-resultat"""
    
    def __init__(self, match_id: int, reporter_id: int, winner_id: int, score_p1: int, score_p2: int):
        super().__init__(timeout=300)  # 5 minuter timeout
        self.match_id = match_id
        self.reporter_id = reporter_id
        self.winner_id = winner_id
        self.score_p1 = score_p1
        self.score_p2 = score_p2
        self.confirmed = False
    
    @discord.ui.button(label='Bekräfta ✅', style=discord.ButtonStyle.green)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Bekräfta resultat"""
        
        async with async_session() as session:
            try:
                match = await session.get(Match, self.match_id)
                
                if not match:
                    await interaction.response.send_message(
                        embed=create_error_embed('Matchen hittades inte!'),
                        ephemeral=True
                    )
                    return
                
                # Kolla att användaren är deltagare i matchen
                if interaction.user.id not in [match.participant1_id, match.participant2_id]:
                    await interaction.response.send_message(
                        embed=create_error_embed('Du är inte deltagare i denna match!'),
                        ephemeral=True
                    )
                    return
                
                # Kolla att det inte är samma person som rapporterade
                if interaction.user.id == self.reporter_id:
                    await interaction.response.send_message(
                        embed=create_error_embed('Du kan inte bekräfta ditt eget resultat!'),
                        ephemeral=True
                    )
                    return
                
                # Uppdatera match
                match.winner_id = self.winner_id
                match.score_p1 = self.score_p1
                match.score_p2 = self.score_p2
                match.status = MatchStatus.COMPLETED
                match.completed_at = datetime.utcnow()
                
                # Hämta spelare/teams
                from database.models import Team
                
                # Kolla om detta är en team-match
                tournament = await session.get(Tournament, match.tournament_id)
                is_team_tournament = tournament.game_mode in ['2v2', '5v5']
                
                if is_team_tournament:
                    # Team match - uppdatera team ELO
                    winner_team = await session.get(Team, self.winner_id)
                    loser_id = match.participant1_id if self.winner_id == match.participant2_id else match.participant2_id
                    loser_team = await session.get(Team, loser_id)
                    
                    if winner_team and loser_team:
                        # Beräkna nya ELO ratings
                        new_winner_elo, new_loser_elo = calculate_elo(
                            winner_team.elo_rating,
                            loser_team.elo_rating,
                            winner_team.total_wins + winner_team.total_losses
                        )
                        
                        # Uppdatera statistik
                        winner_team.elo_rating = new_winner_elo
                        winner_team.total_wins += 1
                        
                        loser_team.elo_rating = new_loser_elo
                        loser_team.total_losses += 1
                        
                        elo_text = f"\n\n**ELO Ändringar:**\n"
                        elo_text += f"🏆 **{winner_team.name}**: {elo_change_description(winner_team.elo_rating - (new_winner_elo - winner_team.elo_rating), new_winner_elo)}\n"
                        elo_text += f"💔 **{loser_team.name}**: {elo_change_description(loser_team.elo_rating - (new_loser_elo - loser_team.elo_rating), new_loser_elo)}"
                    else:
                        elo_text = ""
                else:
                    # Individual match - uppdatera spelare ELO
                    winner = await session.get(Player, self.winner_id)
                    loser_id = match.participant1_id if self.winner_id == match.participant2_id else match.participant2_id
                    loser = await session.get(Player, loser_id)
                    
                    if winner and loser:
                        # Beräkna nya ELO ratings
                        new_winner_elo, new_loser_elo = calculate_elo(
                            winner.elo_rating, 
                            loser.elo_rating, 
                            winner.total_matches
                        )
                        
                        # Uppdatera statistik
                        winner.elo_rating = new_winner_elo
                        winner.total_matches += 1
                        winner.total_wins += 1
                        
                        loser.elo_rating = new_loser_elo
                        loser.total_matches += 1
                        loser.total_losses += 1
                        
                        elo_text = f"\n\n**ELO Ändringar:**\n"
                        elo_text += f"🏆 <@{winner.user_id}>: {elo_change_description(winner.elo_rating - (new_winner_elo - winner.elo_rating), new_winner_elo)}\n"
                        elo_text += f"💔 <@{loser.user_id}>: {elo_change_description(loser.elo_rating - (new_loser_elo - loser.elo_rating), new_loser_elo)}"
                    else:
                        elo_text = ""
                
                # Efter ELO uppdatering, lägg till match history
                if not is_team_tournament:
                    # Spara match history för båda spelare
                    winner_history = MatchHistory(
                        match_id=self.match_id,
                        user_id=self.winner_id,
                        opponent_id=loser_id,
                        won=True,
                        elo_change=new_winner_elo - winner.elo_rating,
                        elo_before=winner.elo_rating - (new_winner_elo - winner.elo_rating),
                        elo_after=new_winner_elo,
                        tournament_id=match.tournament_id
                    )
                    
                    loser_history = MatchHistory(
                        match_id=self.match_id,
                        user_id=loser_id,
                        opponent_id=self.winner_id,
                        won=False,
                        elo_change=new_loser_elo - loser.elo_rating,
                        elo_before=loser.elo_rating - (new_loser_elo - loser.elo_rating),
                        elo_after=new_loser_elo,
                        tournament_id=match.tournament_id
                    )
                    
                    session.add(winner_history)
                    session.add(loser_history)
                    
                    # Uppdatera win streak
                    winner.win_streak += 1
                    if winner.win_streak > winner.best_win_streak:
                        winner.best_win_streak = winner.win_streak
                    
                    loser.win_streak = 0
                    
                    # Uppdatera highest ELO
                    if new_winner_elo > winner.highest_elo:
                        winner.highest_elo = new_winner_elo
                    
                    # Uppdatera season stats om säsong är aktiv
                    from database.models import Season, SeasonStats
                    active_season = await session.execute(
                        select(Season).where(
                            Season.guild_id == interaction.guild_id,
                            Season.is_active == True
                        )
                    )
                    season = active_season.scalar_one_or_none()
                    
                    if season:
                        # Winner season stats
                        winner_season = await session.execute(
                            select(SeasonStats).where(
                                SeasonStats.season_id == season.id,
                                SeasonStats.user_id == self.winner_id
                            )
                        )
                        winner_s = winner_season.scalar_one_or_none()
                        if winner_s:
                            winner_s.elo_rating = new_winner_elo
                            winner_s.matches_played += 1
                            winner_s.wins += 1
                            if new_winner_elo > winner_s.highest_elo:
                                winner_s.highest_elo = new_winner_elo
                        
                        # Loser season stats
                        loser_season = await session.execute(
                            select(SeasonStats).where(
                                SeasonStats.season_id == season.id,
                                SeasonStats.user_id == loser_id
                            )
                        )
                        loser_s = loser_season.scalar_one_or_none()
                        if loser_s:
                            loser_s.elo_rating = new_loser_elo
                            loser_s.matches_played += 1
                            loser_s.losses += 1
                
                # Efter match history sparas, lägg till achievement checks
                    achievements_cog = interaction.client.get_cog('AchievementsCog')
                    if achievements_cog:
                        # Check first win
                        if winner.total_wins == 1:
                            await achievements_cog.check_and_award_achievements(
                                self.winner_id, 
                                interaction.guild_id, 
                                'first_win'
                            )
                        
                        # Check win streak
                        await achievements_cog.check_and_award_achievements(
                            self.winner_id,
                            interaction.guild_id,
                            'win_streak'
                        )
                        
                        # Check ELO milestone
                        await achievements_cog.check_and_award_achievements(
                            self.winner_id,
                            interaction.guild_id,
                            'elo_milestone'
                        )
                        
                        # Check matches played
                        await achievements_cog.check_and_award_achievements(
                            self.winner_id,
                            interaction.guild_id,
                            'matches_played'
                        )
                        
                        # Check underdog win
                        elo_diff = loser.elo_rating - winner.elo_rating
                        if elo_diff > 0:
                            await achievements_cog.check_and_award_achievements(
                                self.winner_id,
                                interaction.guild_id,
                                'underdog_win',
                                elo_difference=elo_diff
                            )
                
                # Hantera nästa match i bracket (om single elimination)
                tournament = await session.get(Tournament, match.tournament_id)
                
                if tournament.game_type == 'single_elim':
                    # Hämta alla matcher
                    all_matches_result = await session.execute(
                        select(Match).where(Match.tournament_id == match.tournament_id)
                    )
                    all_matches = list(all_matches_result.scalars().all())
                    
                    # Skapa nästa match
                    next_match = advance_winner(all_matches, match, self.winner_id)
                    
                    if next_match:
                        # Kolla om matchen redan finns i databasen
                        existing = await session.execute(
                            select(Match).where(
                                Match.tournament_id == next_match.tournament_id,
                                Match.round_number == next_match.round_number,
                                Match.match_number == next_match.match_number
                            )
                        )
                        existing_match = existing.scalar_one_or_none()
                        
                        if existing_match:
                            # Uppdatera befintlig match
                            if match.match_number % 2 == 1:
                                existing_match.participant1_id = self.winner_id
                            else:
                                existing_match.participant2_id = self.winner_id
                            
                            # Kolla om båda deltagare är klara, sätt då upp match
                            if existing_match.participant1_id and existing_match.participant2_id:
                                await session.commit()  # Commit först
                                
                                # Auto-setup nästa match
                                guild = interaction.guild
                                voice_cog = interaction.client.get_cog('VoiceCog')
                                
                                if voice_cog and existing_match.status == MatchStatus.PENDING:
                                    team1_ch, team2_ch = await voice_cog.create_match_channels(
                                        guild, existing_match, tournament
                                    )
                                    
                                    if team1_ch and team2_ch:
                                        existing_match.voice_channel_1_id = team1_ch.id
                                        existing_match.voice_channel_2_id = team2_ch.id
                                        existing_match.status = MatchStatus.ONGOING
                                        existing_match.started_at = datetime.utcnow()
                                        
                                        # Notifiera spelare
                                        await interaction.channel.send(
                                            f"🎮 <@{existing_match.participant1_id}> <@{existing_match.participant2_id}>\n\n"
                                            f"**Match {existing_match.match_number}, Round {existing_match.round_number}** är redo!\n"
                                            f"🔵 Team 1: {team1_ch.mention}\n"
                                            f"🔴 Team 2: {team2_ch.mention}"
                                        )
                        else:
                            # Lägg till ny match
                            session.add(next_match)
                        
                        next_match_text = f"\n\n✅ <@{self.winner_id}> går vidare till **Round {next_match.round_number}, Match {next_match.match_number}**!"
                    else:
                        # Kolla om detta var finalen
                        winner_id = get_tournament_winner(all_matches)
                        if winner_id:
                            tournament.status = TournamentStatus.COMPLETED
                            
                            # Uppdatera vinnares statistik
                            if winner:
                                winner.tournaments_won += 1
                            
                            # Spara champion history
                            champion = ChampionHistory(
                                tournament_id=tournament.id,
                                winner_id=winner_id,
                                winner_type=ParticipantType.USER,
                                prize_awarded=tournament.prize_description
                            )
                            session.add(champion)

                            # Check tournament achievements
                            achievements_cog = interaction.client.get_cog('AchievementsCog')
                            if achievements_cog:
                                await achievements_cog.check_and_award_achievements(
                                    winner_id,
                                    interaction.guild_id,
                                    'tournament_win'
                                )
                                
                                await achievements_cog.check_and_award_achievements(
                                    winner_id,
                                    interaction.guild_id,
                                    'tournaments_played'
                                )
                            
                            next_match_text = f"\n\n🏆 **TURNERING AVSLUTAD!**\n🎉 Grattis <@{winner_id}> - Du vann **{tournament.name}**!"
                        else:
                            next_match_text = ""
                else:
                    next_match_text = ""
                
                await session.commit()
                
                # Cleanup voice channels (lägg till denna)
                await cleanup_voice_after_match(
                    interaction.client, 
                    interaction.guild_id, 
                    self.match_id
                )

                # Disable buttons
                for item in self.children:
                    item.disabled = True
                
                await interaction.message.edit(view=self)
                
                await interaction.response.send_message(
                    embed=create_success_embed(
                        f"✅ Match resultat bekräftat!\n\n"
                        f"**Vinnare:** <@{self.winner_id}>\n"
                        f"**Resultat:** {self.score_p1} - {self.score_p2}"
                        f"{elo_text}"
                        f"{next_match_text}"
                    )
                )
                
                logger.info(f'Match {self.match_id} bekräftad av {interaction.user.name}')
                
            except Exception as e:
                logger.error(f'Fel vid bekräftelse av match: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte bekräfta resultat: {str(e)}'),
                    ephemeral=True
                )
    
    @discord.ui.button(label='Avvisa ❌', style=discord.ButtonStyle.red)
    async def deny_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Avvisa resultat"""
        
        async with async_session() as session:
            try:
                match = await session.get(Match, self.match_id)
                
                if not match:
                    await interaction.response.send_message(
                        embed=create_error_embed('Matchen hittades inte!'),
                        ephemeral=True
                    )
                    return
                
                # Kolla att användaren är deltagare i matchen
                if interaction.user.id not in [match.participant1_id, match.participant2_id]:
                    await interaction.response.send_message(
                        embed=create_error_embed('Du är inte deltagare i denna match!'),
                        ephemeral=True
                    )
                    return
                
                # Sätt match som disputed
                match.status = MatchStatus.DISPUTED
                await session.commit()
                
                # Disable buttons
                for item in self.children:
                    item.disabled = True
                
                await interaction.message.edit(view=self)
                
                await interaction.response.send_message(
                    embed=create_error_embed(
                        f"⚠️ Match resultat avvisat!\n\n"
                        f"Matchen är nu markerad som **tvistad**.\n"
                        f"Kontakta en admin för att lösa tvisten."
                    )
                )
                
                logger.info(f'Match {self.match_id} avvisad av {interaction.user.name}')
                
            except Exception as e:
                logger.error(f'Fel vid avvisning av match: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte avvisa resultat: {str(e)}'),
                    ephemeral=True
                )

class MatchCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="report-win", description="Rapportera vinst för en match")
    @app_commands.describe(
        match_id="Match-ID",
        score_winner="Poäng för vinnaren",
        score_loser="Poäng för förloraren"
    )
    async def report_win(
        self, 
        interaction: discord.Interaction, 
        match_id: int,
        score_winner: int = 1,
        score_loser: int = 0
    ):
        """Rapportera att du vann en match"""
        
        async with async_session() as session:
            try:
                match = await session.get(Match, match_id)
                
                if not match:
                    await interaction.response.send_message(
                        embed=create_error_embed('Matchen hittades inte!'),
                        ephemeral=True
                    )
                    return
                
                # Kolla att användaren är deltagare
                if interaction.user.id not in [match.participant1_id, match.participant2_id]:
                    await interaction.response.send_message(
                        embed=create_error_embed('Du är inte deltagare i denna match!'),
                        ephemeral=True
                    )
                    return
                
                # Kolla status
                if match.status == MatchStatus.COMPLETED:
                    await interaction.response.send_message(
                        embed=create_error_embed('Matchen är redan avslutad!'),
                        ephemeral=True
                    )
                    return
                
                if match.status == MatchStatus.DISPUTED:
                    await interaction.response.send_message(
                        embed=create_error_embed('Matchen är tvistad! Kontakta en admin.'),
                        ephemeral=True
                    )
                    return
                
                # Bestäm scores baserat på vem som rapporterar
                winner_id = interaction.user.id
                if match.participant1_id == winner_id:
                    score_p1 = score_winner
                    score_p2 = score_loser
                else:
                    score_p1 = score_loser
                    score_p2 = score_winner
                
                # Hämta opponent för notis
                opponent_id = match.participant2_id if match.participant1_id == winner_id else match.participant1_id
                
                # Skapa bekräftelse-view
                view = MatchResultView(match_id, interaction.user.id, winner_id, score_p1, score_p2)
                
                embed = discord.Embed(
                    title="⚠️ Bekräfta Match Resultat",
                    description=f"<@{interaction.user.id}> rapporterar vinst i **Match {match.match_number}**\n\n"
                                f"**Resultat:** {score_p1} - {score_p2}\n"
                                f"**Vinnare:** <@{winner_id}>\n\n"
                                f"<@{opponent_id}>, bekräfta eller avvisa resultatet:",
                    color=discord.Color.orange(),
                    timestamp=datetime.utcnow()
                )
                
                await interaction.response.send_message(
                    content=f"<@{opponent_id}>",
                    embed=embed,
                    view=view
                )
                
                logger.info(f'{interaction.user.name} rapporterade vinst för match {match_id}')
                
            except Exception as e:
                logger.error(f'Fel vid rapportering av vinst: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte rapportera vinst: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="match-info", description="Visa information om en match")
    @app_commands.describe(match_id="Match-ID")
    async def match_info(self, interaction: discord.Interaction, match_id: int):
        """Visa match information"""
        
        async with async_session() as session:
            try:
                match = await session.get(Match, match_id)
                
                if not match:
                    await interaction.response.send_message(
                        embed=create_error_embed('Matchen hittades inte!'),
                        ephemeral=True
                    )
                    return
                
                # Hämta spelare
                p1 = await session.get(Player, match.participant1_id)
                p2 = await session.get(Player, match.participant2_id)
                
                p1_name = p1.username if p1 else f"Deltagare {match.participant1_id}"
                p2_name = p2.username if p2 else f"Deltagare {match.participant2_id}"
                
                p1_elo = p1.elo_rating if p1 else None
                p2_elo = p2.elo_rating if p2 else None
                
                embed = create_match_embed(match, p1_name, p2_name, p1_elo, p2_elo)
                
                # Lägg till extra info
                tournament = await session.get(Tournament, match.tournament_id)
                if tournament:
                    embed.add_field(
                        name="🏆 Turnering",
                        value=tournament.name,
                        inline=False
                    )
                
                if match.started_at:
                    embed.add_field(
                        name="⏰ Startad",
                        value=f"<t:{int(match.started_at.timestamp())}:R>",
                        inline=True
                    )
                
                if match.completed_at:
                    embed.add_field(
                        name="✅ Avslutad",
                        value=f"<t:{int(match.completed_at.timestamp())}:R>",
                        inline=True
                    )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            except Exception as e:
                logger.error(f'Fel vid hämtning av match info: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte hämta match info: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="my-matches", description="Visa dina aktiva matcher")
    async def my_matches(self, interaction: discord.Interaction):
        """Visa användarens aktiva matcher"""
        
        async with async_session() as session:
            try:
                # Hämta användarens matcher
                result = await session.execute(
                    select(Match, Tournament).join(
                        Tournament, Match.tournament_id == Tournament.id
                    ).where(
                        or_(
                            Match.participant1_id == interaction.user.id,
                            Match.participant2_id == interaction.user.id
                        ),
                        Match.status.in_([MatchStatus.PENDING, MatchStatus.ONGOING]),
                        Tournament.guild_id == interaction.guild_id
                    )
                )
                
                matches = result.all()
                
                if not matches:
                    await interaction.response.send_message(
                        embed=create_error_embed('Du har inga aktiva matcher!'),
                        ephemeral=True
                    )
                    return
                
                embed = discord.Embed(
                    title="🎮 Dina Matcher",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                
                for match, tournament in matches:
                    opponent_id = match.participant2_id if match.participant1_id == interaction.user.id else match.participant1_id
                    opponent = await session.get(Player, opponent_id)
                    opponent_name = opponent.username if opponent else f"Deltagare {opponent_id}"
                    
                    status_emoji = {
                        'pending': '⏳',
                        'ongoing': '🎮'
                    }
                    
                    embed.add_field(
                        name=f"{status_emoji.get(match.status.value, '❓')} Match {match.match_number} - {tournament.name}",
                        value=f"**Opponent:** {opponent_name}\n"
                              f"**Round:** {match.round_number}\n"
                              f"**Match ID:** {match.id}\n"
                              f"*Använd `/report-win {match.id}` för att rapportera vinst*",
                        inline=False
                    )
                
                embed.set_footer(text=f"{len(matches)} aktiva matcher")
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            except Exception as e:
                logger.error(f'Fel vid hämtning av matcher: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte hämta matcher: {str(e)}'),
                    ephemeral=True
                )
    
    @app_commands.command(name="resolve-dispute", description="[ADMIN] Lös en tvistad match")
    @app_commands.describe(
        match_id="Match-ID",
        winner_id="Vinnares User ID",
        score_p1="Poäng för deltagare 1",
        score_p2="Poäng för deltagare 2"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def resolve_dispute(
        self,
        interaction: discord.Interaction,
        match_id: int,
        winner_id: int,
        score_p1: int,
        score_p2: int
    ):
        """Admin kan manuellt lösa tvistade matcher"""
        
        async with async_session() as session:
            try:
                match = await session.get(Match, match_id)
                
                if not match:
                    await interaction.response.send_message(
                        embed=create_error_embed('Matchen hittades inte!'),
                        ephemeral=True
                    )
                    return
                
                # Uppdatera match
                match.winner_id = winner_id
                match.score_p1 = score_p1
                match.score_p2 = score_p2
                match.status = MatchStatus.COMPLETED
                match.completed_at = datetime.utcnow()
                
                # Uppdatera ELO och stats (samma logik som i bekräftelse)
                winner = await session.get(Player, winner_id)
                loser_id = match.participant1_id if winner_id == match.participant2_id else match.participant2_id
                loser = await session.get(Player, loser_id)
                
                if winner and loser:
                    new_winner_elo, new_loser_elo = calculate_elo(
                        winner.elo_rating,
                        loser.elo_rating,
                        winner.total_matches
                    )
                    
                    winner.elo_rating = new_winner_elo
                    winner.total_matches += 1
                    winner.total_wins += 1
                    
                    loser.elo_rating = new_loser_elo
                    loser.total_matches += 1
                    loser.total_losses += 1
                
                await session.commit()
                
                await interaction.response.send_message(
                    embed=create_success_embed(
                        f"✅ Match {match_id} löst!\n\n"
                        f"**Vinnare:** <@{winner_id}>\n"
                        f"**Resultat:** {score_p1} - {score_p2}"
                    )
                )
                
                logger.info(f'Admin {interaction.user.name} löste match {match_id}')
                
            except Exception as e:
                logger.error(f'Fel vid lösning av match: {e}', exc_info=True)
                await interaction.response.send_message(
                    embed=create_error_embed(f'Kunde inte lösa match: {str(e)}'),
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(MatchCog(bot))