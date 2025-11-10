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
    if elo < 300:
        return "🥉 Brons I"
    elif elo < 450:
        return "🥉🥉 Brons II"
    elif elo < 600:
        return "🥉🥉🥉 Brons III"
    elif elo < 750:
        return "🥈 Silver I"
    elif elo < 900:
        return "🥈🥈 Silver II"
    elif elo < 1100:
        return "🥈🥈🥈 Silver III"
    elif elo < 1250:
        return "🥇 Guld I"
    elif elo < 1400:
        return "🥇🥇 Guld II"
    elif elo < 1700:
        return "🥇🥇🥇 Guld III"
    elif elo < 1950:
        return "💠 Platinum I"
    elif elo < 2200:
        return "💠💠 Platinum II"
    elif elo < 2350:
        return "💠💠💠 Platinum III"
    elif elo < 2500:
        return "💎 Diamant I"
    elif elo < 2650:
        return "💎💎 Diamant II"
    elif elo < 2850:
        return "💎💎💎 Diamant III"
    elif elo < 3000:
        return "🌟 Mästare"
    elif elo < 3200:
        return "🌟🌟 Mästarnas Mästare"
    else:
        return "👑 Proffs"

def convert_premier_to_elo(premier_elo: int) -> int:
    """
    Konvertera CS2 Premier ELO till vårt ELO system.
    
    Översättning:
    - 1k Premier = 150 ELO
    - 5k Premier = 600 ELO
    - 10k Premier = 1100 ELO
    - 15k Premier = 1700 ELO
    - 20k Premier = 2350 ELO
    - 25k Premier = 2850 ELO
    - 29k Premier = 3050 ELO
    """
    
    # Klampa premier_elo mellan 0 och 35000
    premier_elo = max(0, min(35000, premier_elo))
    
    # Linjär interpolation mellan brytpunkterna
    breakpoints = [
        (0, 0),
        (1000, 150),
        (5000, 600),
        (10000, 1100),
        (15000, 1700),
        (20000, 2350),
        (25000, 2850),
        (29000, 3050),
        (35000, 3500)  # Max cap
    ]
    
    # Hitta vilket intervall vi är i
    for i in range(len(breakpoints) - 1):
        premier_low, elo_low = breakpoints[i]
        premier_high, elo_high = breakpoints[i + 1]
        
        if premier_low <= premier_elo <= premier_high:
            # Linjär interpolation
            ratio = (premier_elo - premier_low) / (premier_high - premier_low)
            our_elo = elo_low + ratio * (elo_high - elo_low)
            return round(our_elo)
    
    return 1000  # Fallback

def convert_faceit_to_elo(faceit_level: int, faceit_elo: int = 1000) -> int:
    """
    Konvertera Faceit Level + ELO till vårt ELO system.
    
    Översättning:
    - Level 1 = 150 ELO
    - Level 2 = 600 ELO
    - Level 3 = 1100 ELO
    - Level 7 = 1700 ELO
    - Level 10 (1000-2300) = 2350 ELO
    - Level 10 (2300-2600) = 2850 ELO
    - Level 10 (2600+) = 3050 ELO
    """
    
    # Base ELO från level
    level_elo_map = {
        1: 150,
        2: 600,
        3: 1100,
        4: 1250,
        5: 1400,
        6: 1550,
        7: 1700,
        8: 1900,
        9: 2100,
        10: 2350  # Base för level 10
    }
    
    base_elo = level_elo_map.get(faceit_level, 1000)
    
    # Extra justering för level 10 baserat på faceit ELO
    if faceit_level == 10:
        if faceit_elo >= 2600:
            return 3050
        elif faceit_elo >= 2300:
            return 2850
        else:
            return 2350
    
    return base_elo

def get_elo_tier_color(elo: int) -> int:
    """Få färg baserat på ELO tier (för embeds)"""
    if elo < 600:
        return 0xCD7F32  # Brons
    elif elo < 1100:
        return 0xC0C0C0  # Silver
    elif elo < 1700:
        return 0xFFD700  # Guld
    elif elo < 2350:
        return 0xE5E4E2  # Platinum
    elif elo < 2850:
        return 0xB9F2FF  # Diamant
    elif elo < 3000:
        return 0xFFA500  # Mästare
    else:
        return 0xFF1493  # Proffs

def validate_premier_elo(premier_elo: int) -> bool:
    """Validera att Premier ELO är inom rimligt intervall"""
    return 0 <= premier_elo <= 35000

def validate_faceit_level(level: int) -> bool:
    """Validera att Faceit level är giltig"""
    return 1 <= level <= 10

def validate_faceit_elo(elo: int) -> bool:
    """Validera att Faceit ELO är inom rimligt intervall"""
    return 500 <= elo <= 3500