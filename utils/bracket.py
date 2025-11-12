import math
from typing import List, Tuple, Optional
from database.models import Match, TournamentParticipant, MatchStatus
import random

async def get_participant_name(session, participant_id: int, participant_type) -> str:
    """Hämta namn för en deltagare (user eller team)"""
    from database.models import Player, Team, ParticipantType
    
    if participant_type == ParticipantType.TEAM:
        team = await session.get(Team, participant_id)
        return team.name if team else f"Team {participant_id}"
    else:
        player = await session.get(Player, participant_id)
        return player.username if player else f"Spelare {participant_id}"

async def get_participant_display_name(session, participant_id: int, participant_type, game_mode: str) -> str:
    """
    Hämta visningsnamn för en deltagare
    
    Args:
        session: Database session
        participant_id: ID för deltagare
        participant_type: USER eller TEAM
        game_mode: Spelläge (för att avgöra om team eller inte)
    
    Returns:
        Formaterat visningsnamn
    """
    from database.models import Player, Team, ParticipantType
    
    is_team_tournament = game_mode in ['2v2', '5v5']
    
    if is_team_tournament:
        team = await session.get(Team, participant_id)
        if team:
            if team.tag:
                return f"[{team.tag}] {team.name}"
            return team.name
        return f"Team {participant_id}"
    else:
        player = await session.get(Player, participant_id)
        if player:
            return player.username
        return f"Spelare {participant_id}"

async def get_participant_elo(session, participant_id: int, participant_type) -> int:
    """Hämta ELO för en deltagare (user eller team)"""
    from database.models import Player, Team, ParticipantType
    
    if participant_type == ParticipantType.TEAM:
        team = await session.get(Team, participant_id)
        return team.elo_rating if team else 1000
    else:
        player = await session.get(Player, participant_id)
        return player.elo_rating if player else 1000

def generate_single_elimination(tournament_id: int, participants: List[TournamentParticipant]) -> List[Match]:
    """
    Generera single elimination bracket.
    
    Args:
        tournament_id: Turnerings-ID
        participants: Lista med anmälda deltagare
    
    Returns:
        Lista med Match-objekt för första rundan
    """
    
    num_participants = len(participants)
    
    if num_participants < 2:
        raise ValueError("Minst 2 deltagare krävs för en turnering!")
    
    # Beräkna antal rounds
    num_rounds = math.ceil(math.log2(num_participants))
    bracket_size = 2 ** num_rounds
    
    # Seed deltagare
    seeded = seed_participants(participants, method='elo')
    
    # Lägg till byes om nödvändigt
    byes_needed = bracket_size - num_participants
    
    matches = []
    match_number = 1
    
    # Skapa första rundan
    for i in range(0, bracket_size, 2):
        p1 = seeded[i] if i < len(seeded) else None
        p2 = seeded[i + 1] if i + 1 < len(seeded) else None
        
        match = Match(
            tournament_id=tournament_id,
            round_number=1,
            match_number=match_number,
            participant1_id=p1.participant_id if p1 else None,
            participant2_id=p2.participant_id if p2 else None,
            status=MatchStatus.PENDING
        )
        
        # Om någon är None (BYE), automatisk vinst
        if p1 and not p2:
            match.winner_id = p1.participant_id
            match.status = MatchStatus.COMPLETED
            match.score_p1 = 1
            match.score_p2 = 0
        elif p2 and not p1:
            match.winner_id = p2.participant_id
            match.status = MatchStatus.COMPLETED
            match.score_p1 = 0
            match.score_p2 = 1
        
        matches.append(match)
        match_number += 1
    
    return matches

def generate_round_robin(tournament_id: int, participants: List[TournamentParticipant]) -> List[Match]:
    """
    Generera round robin bracket (alla möter alla).
    
    Args:
        tournament_id: Turnerings-ID
        participants: Lista med anmälda deltagare
    
    Returns:
        Lista med alla matcher
    """
    
    num_participants = len(participants)
    
    if num_participants < 2:
        raise ValueError("Minst 2 deltagare krävs för en turnering!")
    
    matches = []
    match_number = 1
    
    # Generera alla möjliga matchups
    for i in range(num_participants):
        for j in range(i + 1, num_participants):
            match = Match(
                tournament_id=tournament_id,
                round_number=1,  # Alla matcher i samma "round"
                match_number=match_number,
                participant1_id=participants[i].participant_id,
                participant2_id=participants[j].participant_id,
                status=MatchStatus.PENDING
            )
            matches.append(match)
            match_number += 1
    
    return matches

def seed_participants(participants: List[TournamentParticipant], method: str = 'elo') -> List[TournamentParticipant]:
    """
    Seed deltagare för bracket.
    
    Methods:
        - 'elo': Sortera efter ELO rating (behöver Player data)
        - 'random': Slumpmässig
        - 'signup': First come first serve
    """
    
    if method == 'random':
        shuffled = participants.copy()
        random.shuffle(shuffled)
        return shuffled
    elif method == 'signup':
        return sorted(participants, key=lambda p: p.signup_time)
    else:  # default elo - för nu använder vi signup ordning
        # TODO: Implementera ELO-baserad seeding när vi har Player relations
        return sorted(participants, key=lambda p: p.signup_time)
    
async def seed_participants_by_elo(session, participants: List[TournamentParticipant]) -> List[TournamentParticipant]:
    """Seed deltagare baserat på ELO"""
    # Skapa lista med (participant, elo)
    participant_elos = []
    
    for p in participants:
        elo = await get_participant_elo(session, p.participant_id, p.participant_type)
        participant_elos.append((p, elo))
    
    # Sortera efter ELO (högst först)
    participant_elos.sort(key=lambda x: x[1], reverse=True)
    
    return [p[0] for p in participant_elos]

def advance_winner(matches: List[Match], completed_match: Match, winner_id: int) -> Optional[Match]:
    """
    Hitta eller skapa nästa match för vinnare i single elimination.
    
    Args:
        matches: Alla matcher i turneringen
        completed_match: Den avslutade matchen
        winner_id: ID för vinnaren
    
    Returns:
        Nästa match som vinnaren ska spela, eller None om final
    """
    
    next_round = completed_match.round_number + 1
    next_match_number = (completed_match.match_number + 1) // 2
    
    # Hitta om next match redan finns
    next_match = None
    for match in matches:
        if match.round_number == next_round and match.match_number == next_match_number:
            next_match = match
            break
    
    if not next_match:
        # Skapa ny match för nästa round
        next_match = Match(
            tournament_id=completed_match.tournament_id,
            round_number=next_round,
            match_number=next_match_number,
            status=MatchStatus.PENDING
        )
    
    # Sätt vinnare i rätt slot (udda match = participant1, jämn = participant2)
    if completed_match.match_number % 2 == 1:
        next_match.participant1_id = winner_id
    else:
        next_match.participant2_id = winner_id
    
    return next_match

def calculate_total_rounds(num_participants: int, bracket_type: str) -> int:
    """Beräkna totalt antal rounds för en turnering"""
    if bracket_type == 'single_elim':
        return math.ceil(math.log2(num_participants))
    elif bracket_type == 'round_robin':
        return 1  # Alla matcher i samma "round"
    elif bracket_type == 'double_elim':
        # Winner bracket + Loser bracket + Grand Finals
        return math.ceil(math.log2(num_participants)) * 2 + 1
    return 1

def get_bracket_structure(tournament_id: int, matches: List[Match]) -> dict:
    """
    Organisera matcher i en bracket-struktur för visualisering.
    
    Returns:
        Dictionary med rounds och matcher
    """
    
    if not matches:
        return {}
    
    # Gruppera matcher per round
    rounds = {}
    for match in matches:
        if match.round_number not in rounds:
            rounds[match.round_number] = []
        rounds[match.round_number].append(match)
    
    # Sortera matcher inom varje round
    for round_num in rounds:
        rounds[round_num] = sorted(rounds[round_num], key=lambda m: m.match_number)
    
    return rounds

def is_bracket_complete(matches: List[Match]) -> bool:
    """Kolla om alla matcher i bracket är avslutade"""
    return all(m.status == MatchStatus.COMPLETED for m in matches)

def get_tournament_winner(matches: List[Match]) -> Optional[int]:
    """
    Hitta vinnaren av turneringen (sista matchens vinnare).
    
    Returns:
        Winner ID eller None om turneringen inte är klar
    """
    
    if not matches:
        return None
    
    # Hitta högsta round number
    max_round = max(m.round_number for m in matches)
    
    # Hitta finalen (högsta round, match 1)
    final_match = None
    for match in matches:
        if match.round_number == max_round and match.match_number == 1:
            final_match = match
            break
    
    if final_match and final_match.status == MatchStatus.COMPLETED:
        return final_match.winner_id
    
    return None

def generate_swiss(tournament_id: int, participants: List[TournamentParticipant], round_number: int, previous_results: List[Match]) -> List[Match]:
    """
    Generate Swiss tournament pairings for a given round.

    Args:
        tournament_id: The ID of the tournament.
        participants: List of participants in the tournament.
        round_number: The current round number.
        previous_results: List of matches from previous rounds.

    Returns:
        List of matches for the current round.
    """
    # Calculate scores based on previous results
    scores = {p.participant_id: 0 for p in participants}
    for match in previous_results:
        if match.winner_id:
            scores[match.winner_id] += 1

    # Sort participants by scores (descending)
    sorted_participants = sorted(participants, key=lambda p: scores[p.participant_id], reverse=True)

    # Pair participants with similar scores
    matches = []
    match_number = 1
    while len(sorted_participants) > 1:
        p1 = sorted_participants.pop(0)
        p2 = sorted_participants.pop(0)

        match = Match(
            tournament_id=tournament_id,
            round_number=round_number,
            match_number=match_number,
            participant1_id=p1.participant_id,
            participant2_id=p2.participant_id,
            status=MatchStatus.PENDING
        )
        matches.append(match)
        match_number += 1

    # Handle odd number of participants (bye)
    if sorted_participants:
        p1 = sorted_participants.pop(0)
        match = Match(
            tournament_id=tournament_id,
            round_number=round_number,
            match_number=match_number,
            participant1_id=p1.participant_id,
            participant2_id=None,  # No opponent
            status=MatchStatus.COMPLETED,
            winner_id=p1.participant_id,
            score_p1=1,
            score_p2=0
        )
        matches.append(match)

    return matches