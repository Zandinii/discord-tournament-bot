def calculate_elo(winner_elo: int, loser_elo: int, winner_matches: int = 0) -> tuple[int, int]:
    """
    Beräkna nya ELO ratings efter en match.
    
    Args:
        winner_elo: Vinnarens nuvarande ELO
        loser_elo: Förlorarens nuvarande ELO
        winner_matches: Antal matcher vinnaren spelat (för K-factor)
    
    Returns:
        Tuple med (ny winner ELO, ny loser ELO)
    """
    
    # Bestäm K-factor baserat på antal matcher
    if winner_matches < 10:
        k_factor = 40  # Nya spelare
    elif winner_matches < 100:
        k_factor = 32  # Etablerade spelare
    else:
        k_factor = 24  # Masters
    
    # Beräkna förväntad vinst-sannolikhet
    expected_winner = 1 / (1 + 10 ** ((loser_elo - winner_elo) / 400))
    expected_loser = 1 - expected_winner
    
    # Beräkna nya ratings
    new_winner_elo = winner_elo + k_factor * (1 - expected_winner)
    new_loser_elo = loser_elo + k_factor * (0 - expected_loser)
    
    return round(new_winner_elo), round(new_loser_elo)

def calculate_team_elo(member_elos: list[int]) -> int:
    """Beräkna team ELO som genomsnitt av medlemmar"""
    if not member_elos:
        return 1000
    return round(sum(member_elos) / len(member_elos))

def elo_change_description(old_elo: int, new_elo: int) -> str:
    """Skapa beskrivning av ELO-förändring"""
    change = new_elo - old_elo
    emoji = "📈" if change > 0 else "📉"
    sign = "+" if change > 0 else ""
    return f"{emoji} {old_elo} → {new_elo} ({sign}{change})"

def get_rank_from_elo(elo: int) -> str:
    """Få rank-namn baserat på ELO"""
    if elo < 800:
        return "🥉 Brons"
    elif elo < 1000:
        return "🥈 Silver"
    elif elo < 1200:
        return "🥇 Guld"
    elif elo < 1400:
        return "💎 Platinum"
    elif elo < 1600:
        return "💠 Diamant"
    elif elo < 1800:
        return "🌟 Mästare"
    else:
        return "👑 Proffs"