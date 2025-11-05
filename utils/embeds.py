import discord
from datetime import datetime
from typing import Optional

def create_tournament_announcement(tournament, participant_count: int = 0) -> discord.Embed:
    """Skapa announcement embed för ny turnering"""
    
    embed = discord.Embed(
        title=f"🏆 {tournament.name}",
        description=tournament.description or f"En ny **{tournament.game_mode}** turnering har skapats!",
        color=discord.Color.gold(),
        timestamp=datetime.utcnow()
    )
    
    # Mode & Type
    game_type_display = tournament.game_type.replace('_', ' ').title()
    embed.add_field(
        name="📋 Format",
        value=f"**Mode:** {tournament.game_mode}\n**Type:** {game_type_display}",
        inline=True
    )
    
    # Players
    embed.add_field(
        name="👥 Deltagare",
        value=f"{participant_count}/{tournament.max_participants}",
        inline=True
    )
    
    # Status
    status_emoji = {
        'signup': '✅ Öppen för anmälan',
        'ongoing': '🎮 Pågående',
        'completed': '✅ Avslutad',
        'cancelled': '❌ Avbruten'
    }
    embed.add_field(
        name="📊 Status",
        value=status_emoji.get(tournament.status.value, '❓'),
        inline=True
    )
    
    # Prize
    if tournament.prize_description:
        embed.add_field(
            name="🎁 Pris",
            value=tournament.prize_description,
            inline=False
        )
    
    # Start time
    timestamp = int(tournament.start_time.timestamp())
    embed.add_field(
        name="⏰ Starttid",
        value=f"<t:{timestamp}:F>\n(<t:{timestamp}:R>)",
        inline=False
    )
    
    embed.set_footer(text=f"Turnerings-ID: {tournament.id} | Använd knapparna nedan för att anmäla dig!")
    
    return embed

def create_match_embed(match, participant1_name: str, participant2_name: str, 
                       p1_elo: Optional[int] = None, p2_elo: Optional[int] = None) -> discord.Embed:
    """Skapa match-kort"""
    
    embed = discord.Embed(
        title=f"⚔️ Match #{match.match_number} - Round {match.round_number}",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    
    # Participant 1
    p1_text = f"**{participant1_name}**"
    if p1_elo:
        p1_text += f"\nELO: {p1_elo}"
    
    embed.add_field(
        name="🔵 Deltagare 1",
        value=p1_text,
        inline=True
    )
    
    embed.add_field(
        name="🆚",
        value="\u200b",
        inline=True
    )
    
    # Participant 2
    p2_text = f"**{participant2_name}**"
    if p2_elo:
        p2_text += f"\nELO: {p2_elo}"
    
    embed.add_field(
        name="🔴 Deltagare 2",
        value=p2_text,
        inline=True
    )
    
    # Status
    status_emoji = {
        'pending': '⏳ Väntar',
        'ongoing': '🎮 Pågående',
        'completed': '✅ Avslutad',
        'disputed': '⚠️ Tvistad'
    }
    embed.add_field(
        name="Status",
        value=status_emoji.get(match.status.value, '❓'),
        inline=False
    )
    
    # Score om completed
    if match.status.value == 'completed' and match.score_p1 is not None:
        embed.add_field(
            name="📊 Resultat",
            value=f"{match.score_p1} - {match.score_p2}",
            inline=False
        )
    
    embed.set_footer(text=f"Match ID: {match.id}")
    
    return embed

def create_player_profile(player, recent_matches: list = None) -> discord.Embed:
    """Skapa spelarprofil"""
    
    win_rate = (player.total_wins / player.total_matches * 100) if player.total_matches > 0 else 0
    
    embed = discord.Embed(
        title=f"👤 {player.username}",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    
    # Stats
    embed.add_field(
        name="📊 Statistik",
        value=f"**ELO:** {player.elo_rating}\n"
              f"**Matcher:** {player.total_matches}\n"
              f"**Vinster:** {player.total_wins}\n"
              f"**Förluster:** {player.total_losses}\n"
              f"**Win Rate:** {win_rate:.1f}%",
        inline=True
    )
    
    # Achievements
    embed.add_field(
        name="🏆 Prestationer",
        value=f"**Turneringar Vunna:** {player.tournaments_won}\n"
              f"**Turneringar Deltagna:** {player.tournaments_participated}",
        inline=True
    )
    
    # Recent matches
    if recent_matches:
        recent_text = "\n".join([
            f"{'✅' if m['won'] else '❌'} vs {m['opponent']}"
            for m in recent_matches[:5]
        ])
        embed.add_field(
            name="📜 Senaste Matcher",
            value=recent_text or "Inga matcher än",
            inline=False
        )
    
    embed.set_footer(text=f"Medlem sedan {player.created_at.strftime('%Y-%m-%d')}")
    
    return embed

def create_leaderboard(players: list, category: str = 'elo') -> discord.Embed:
    """Skapa leaderboard"""
    
    medals = ['🥇', '🥈', '🥉']
    
    category_names = {
        'elo': 'ELO Rating',
        'wins': 'Totala Vinster',
        'tournaments': 'Turneringar Vunna'
    }
    
    embed = discord.Embed(
        title="🏆 Leaderboard",
        description=f"Top spelare sorterat efter **{category_names.get(category, 'ELO')}**",
        color=discord.Color.gold(),
        timestamp=datetime.utcnow()
    )
    
    if not players:
        embed.description += "\n\n*Inga spelare ännu*"
        return embed
    
    leaderboard_text = []
    for i, player in enumerate(players[:10], 1):
        medal = medals[i-1] if i <= 3 else f"`#{i}`"
        
        if category == 'elo':
            value = f"{player.elo_rating} ELO"
        elif category == 'wins':
            value = f"{player.total_wins} vinster"
        elif category == 'tournaments':
            value = f"{player.tournaments_won} turneringar"
        else:
            value = f"{player.elo_rating} ELO"
        
        leaderboard_text.append(f"{medal} **{player.username}** - {value}")
    
    embed.description += "\n\n" + "\n".join(leaderboard_text)
    embed.set_footer(text="Uppdateras automatiskt")
    
    return embed

def create_bracket_embed(tournament, matches: list, current_round: int = 1) -> discord.Embed:
    """Skapa bracket översikt"""
    
    embed = discord.Embed(
        title=f"🏆 {tournament.name} - Bracket",
        description=f"**Round {current_round}**",
        color=discord.Color.gold(),
        timestamp=datetime.utcnow()
    )
    
    if not matches:
        embed.description += "\n\n*Inga matcher ännu*"
        return embed
    
    # Gruppera matcher per round
    round_matches = [m for m in matches if m.round_number == current_round]
    
    for match in round_matches[:10]:  # Max 10 för att inte överbelasta
        status = "⏳" if match.status.value == "pending" else "🎮" if match.status.value == "ongoing" else "✅"
        
        p1_name = f"Deltagare {match.participant1_id}" if match.participant1_id else "BYE"
        p2_name = f"Deltagare {match.participant2_id}" if match.participant2_id else "BYE"
        
        winner_text = ""
        if match.winner_id:
            winner_text = f" → **Vinnare: {match.winner_id}**"
        
        embed.add_field(
            name=f"{status} Match {match.match_number}",
            value=f"{p1_name} vs {p2_name}{winner_text}",
            inline=False
        )
    
    total_rounds = max([m.round_number for m in matches]) if matches else 1
    embed.set_footer(text=f"Round {current_round}/{total_rounds} | Turnerings-ID: {tournament.id}")
    
    return embed

def create_map_ban_embed(
    match_id: int,
    bo_format: int,
    available_maps: list,
    banned_maps: list,
    current_banner_id: int,
    bans_done: int,
    total_bans: int
) -> discord.Embed:
    """Skapa map ban embed"""
    
    embed = discord.Embed(
        title=f"🗺️ Map Ban Phase - Match {match_id}",
        description=f"**Best of {bo_format}**\n\n"
                   f"Bans: {bans_done}/{total_bans}",
        color=discord.Color.orange(),
        timestamp=datetime.utcnow()
    )
    
    # Tillgängliga kartor
    if available_maps:
        embed.add_field(
            name="📋 Tillgängliga Kartor",
            value="\n".join([f"✅ {m}" for m in available_maps]),
            inline=False
        )
    
    # Bannade kartor
    if banned_maps:
        banned_text = "\n".join([
            f"🚫 {b['map']} (Ban #{b['order']})" 
            for b in banned_maps
        ])
        embed.add_field(
            name="🚫 Bannade Kartor",
            value=banned_text,
            inline=False
        )
    else:
        embed.add_field(
            name="🚫 Bannade Kartor",
            value="*Inga bans än*",
            inline=False
        )
    
    # Vems tur
    if bans_done < total_bans:
        embed.add_field(
            name="⏳ Väntar på",
            value=f"<@{current_banner_id}> - 30 sekunder",
            inline=False
        )
    
    embed.set_footer(text=f"Match ID: {match_id} | Endast lagkaptener kan banna")
    
    return embed

def create_map_ban_complete_embed(
    match_id: int,
    bo_format: int,
    maps_to_play: list,
    participant1_id: int,
    participant2_id: int
) -> discord.Embed:
    """Skapa embed när map bans är klara"""
    
    embed = discord.Embed(
        title="✅ Map Ban Phase Klar!",
        description=f"**Best of {bo_format}**",
        color=discord.Color.green(),
        timestamp=datetime.utcnow()
    )
    
    # Visa kartor som ska spelas
    maps_text = ""
    for i, map_info in enumerate(maps_to_play, 1):
        maps_text += f"**Map {i}:** {map_info['map']}\n"
        maps_text += f"├ <@{participant1_id}>: {map_info['side_p1']}\n"
        maps_text += f"└ <@{participant2_id}>: {map_info['side_p2']}\n\n"
    
    embed.add_field(
        name="🗺️ Kartor att Spela",
        value=maps_text,
        inline=False
    )
    
    embed.set_footer(text="Lycka till! Rapportera resultat med /report-win när ni är klara.")
    
    return embed

def create_map_ban_timeout_embed(
    banner_id: int,
    map_name: str
) -> discord.Embed:
    """Skapa embed för timeout"""
    
    embed = discord.Embed(
        title="⏰ Timeout!",
        description=f"<@{banner_id}> fick timeout!\n\n**{map_name}** bannades automatiskt.",
        color=discord.Color.orange(),
        timestamp=datetime.utcnow()
    )
    
    return embed

def create_error_embed(message: str) -> discord.Embed:
    """Skapa error embed"""
    embed = discord.Embed(
        title="❌ Fel",
        description=message,
        color=discord.Color.red()
    )
    return embed

def create_success_embed(message: str) -> discord.Embed:
    """Skapa success embed"""
    embed = discord.Embed(
        title="✅ Klart!",
        description=message,
        color=discord.Color.green()
    )
    return embed