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