from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database.database import Base

# Enums för olika statusar
class TournamentStatus(enum.Enum):
    SIGNUP = "signup"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class MatchStatus(enum.Enum):
    PENDING = "pending"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    DISPUTED = "disputed"

class ParticipantType(enum.Enum):
    USER = "user"
    TEAM = "team"

# Guild Configuration
class Guild(Base):
    __tablename__ = 'guilds'
    
    guild_id = Column(Integer, primary_key=True)
    tournament_channel_id = Column(Integer, nullable=True)
    lobby_voice_channel_id = Column(Integer, nullable=True)
    notification_role_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Guild(guild_id={self.guild_id})>"

# Tournament
class Tournament(Base):
    __tablename__ = 'tournaments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(Integer, ForeignKey('guilds.guild_id'), nullable=False)
    name = Column(String(100), nullable=False)
    game_mode = Column(String(10), nullable=False)  # 1v1, 2v2, 5v5
    game_type = Column(String(20), nullable=False)  # single_elim, double_elim, round_robin
    max_participants = Column(Integer, default=32)
    start_time = Column(DateTime, nullable=False)
    status = Column(Enum(TournamentStatus), default=TournamentStatus.SIGNUP)
    prize_description = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    announcement_message_id = Column(Integer, nullable=True)
    game_name = Column(String(50), nullable=True)  # CS2, Valorant, etc
    bo_format_groupstage = Column(Integer, default=1)  # Best of 1 eller 3 för gruppspel
    bo_format_playoffs = Column(Integer, default=1)  # Best of 1 eller 3 för slutspel
    map_pool = Column(Text, nullable=True)  # JSON string med kartor: ["Dust2", "Mirage", ...]
    season_id = Column(Integer, ForeignKey('seasons.id'), nullable=True)
    
    # Relationships
    participants = relationship("TournamentParticipant", back_populates="tournament", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="tournament", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tournament(id={self.id}, name='{self.name}', status='{self.status.value}')>"

# Player
class Player(Base):
    __tablename__ = 'players'
    
    user_id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, ForeignKey('guilds.guild_id'), nullable=False)
    username = Column(String(100), nullable=False)
    elo_rating = Column(Integer, default=1000)
    total_matches = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    total_losses = Column(Integer, default=0)
    tournaments_won = Column(Integer, default=0)
    tournaments_participated = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    current_season_id = Column(Integer, ForeignKey('seasons.id'), nullable=True)
    highest_elo = Column(Integer, default=1000)
    win_streak = Column(Integer, default=0)
    best_win_streak = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<Player(user_id={self.user_id}, username='{self.username}', elo={self.elo_rating})>"

# Team
class Team(Base):
    __tablename__ = 'teams'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(Integer, ForeignKey('guilds.guild_id'), nullable=False)
    name = Column(String(100), nullable=False)
    tag = Column(String(10), nullable=True)
    captain_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    total_wins = Column(Integer, default=0)
    total_losses = Column(Integer, default=0)
    elo_rating = Column(Integer, default=1000)
    
    # Relationships
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}')>"

# Team Member
class TeamMember(Base):
    __tablename__ = 'team_members'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="members")
    
    def __repr__(self):
        return f"<TeamMember(team_id={self.team_id}, user_id={self.user_id})>"

# Tournament Participant
class TournamentParticipant(Base):
    __tablename__ = 'tournament_participants'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey('tournaments.id', ondelete='CASCADE'), nullable=False)
    participant_id = Column(Integer, nullable=False)  # user_id eller team_id
    participant_type = Column(Enum(ParticipantType), nullable=False)
    signup_time = Column(DateTime, default=datetime.utcnow)
    seed = Column(Integer, nullable=True)
    eliminated = Column(Boolean, default=False)
    
    # Relationships
    tournament = relationship("Tournament", back_populates="participants")
    
    def __repr__(self):
        return f"<TournamentParticipant(tournament_id={self.tournament_id}, participant_id={self.participant_id})>"

# Match
class Match(Base):
    __tablename__ = 'matches'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey('tournaments.id', ondelete='CASCADE'), nullable=False)
    round_number = Column(Integer, nullable=False)
    match_number = Column(Integer, nullable=False)
    participant1_id = Column(Integer, nullable=True)
    participant2_id = Column(Integer, nullable=True)
    winner_id = Column(Integer, nullable=True)
    score_p1 = Column(Integer, nullable=True)
    score_p2 = Column(Integer, nullable=True)
    status = Column(Enum(MatchStatus), default=MatchStatus.PENDING)
    voice_channel_1_id = Column(Integer, nullable=True)
    voice_channel_2_id = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    maps_to_play = Column(Text, nullable=True)  # JSON: [{"map": "Dust2", "side_p1": "CT"}, ...]
    ban_phase_complete = Column(Boolean, default=False)
    ban_message_id_team1 = Column(Integer, nullable=True)  # Embed message i team1 channel
    ban_message_id_team2 = Column(Integer, nullable=True)  # Embed message i team2 channel
    
    # Relationships
    tournament = relationship("Tournament", back_populates="matches")
    
    def __repr__(self):
        return f"<Match(id={self.id}, round={self.round_number}, status='{self.status.value}')>"

# Match Participant (för att spara enskilda spelare i lags-matcher)
class MatchParticipant(Base):
    __tablename__ = 'match_participants'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey('matches.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, nullable=False)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=True)
    side = Column(Integer, nullable=False)  # 1 eller 2
    
    def __repr__(self):
        return f"<MatchParticipant(match_id={self.match_id}, user_id={self.user_id}, side={self.side})>"

# Champion History
class ChampionHistory(Base):
    __tablename__ = 'champion_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey('tournaments.id', ondelete='CASCADE'), nullable=False)
    winner_id = Column(Integer, nullable=False)
    winner_type = Column(Enum(ParticipantType), nullable=False)
    prize_awarded = Column(String(500), nullable=True)
    awarded_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ChampionHistory(tournament_id={self.tournament_id}, winner_id={self.winner_id})>"

# Notification
class Notification(Base):
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey('tournaments.id', ondelete='CASCADE'), nullable=True)
    message = Column(Text, nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Notification(id={self.id}, sent={self.sent})>"
    
class MapBan(Base):
    __tablename__ = 'map_bans'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey('matches.id', ondelete='CASCADE'), nullable=False)
    participant_id = Column(Integer, nullable=False)  # Team eller User ID som bannade
    map_name = Column(String(100), nullable=False)
    ban_order = Column(Integer, nullable=False)  # Ordning av bans
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<MapBan(match_id={self.match_id}, map='{self.map_name}')>"

class Season(Base):
    __tablename__ = 'seasons'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(Integer, ForeignKey('guilds.guild_id'), nullable=False)
    name = Column(String(100), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Season(name='{self.name}', active={self.is_active})>"

class SeasonStats(Base):
    __tablename__ = 'season_stats'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    season_id = Column(Integer, ForeignKey('seasons.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, nullable=False)
    guild_id = Column(Integer, nullable=False)
    elo_rating = Column(Integer, default=1000)
    matches_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    tournaments_played = Column(Integer, default=0)
    tournaments_won = Column(Integer, default=0)
    highest_elo = Column(Integer, default=1000)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<SeasonStats(season_id={self.season_id}, user_id={self.user_id})>"

class MatchHistory(Base):
    __tablename__ = 'match_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey('matches.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, nullable=False)
    opponent_id = Column(Integer, nullable=False)
    won = Column(Boolean, nullable=False)
    elo_change = Column(Integer, nullable=False)
    elo_before = Column(Integer, nullable=False)
    elo_after = Column(Integer, nullable=False)
    tournament_id = Column(Integer, ForeignKey('tournaments.id'), nullable=True)
    played_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<MatchHistory(user_id={self.user_id}, won={self.won})>"
    
class Achievement(Base):
    __tablename__ = 'achievements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500), nullable=False)
    icon = Column(String(50), nullable=True)  # Emoji eller icon name
    requirement_type = Column(String(50), nullable=False)  # wins_streak, tournament_win, elo_milestone, etc
    requirement_value = Column(Integer, nullable=False)
    reward_role_name = Column(String(100), nullable=True)  # Optional Discord role name
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Achievement(name='{self.name}')>"

class PlayerAchievement(Base):
    __tablename__ = 'player_achievements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    guild_id = Column(Integer, nullable=False)
    achievement_id = Column(Integer, ForeignKey('achievements.id', ondelete='CASCADE'), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)
    notified = Column(Boolean, default=False)
    
    # Relationships
    achievement = relationship("Achievement")
    
    def __repr__(self):
        return f"<PlayerAchievement(user_id={self.user_id}, achievement_id={self.achievement_id})>"