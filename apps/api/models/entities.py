"""SQLAlchemy ORM models for SmartBets Pro."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Index, Integer,
    String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from apps.api.core.database import Base


class Sport(Base):
    __tablename__ = "sports"

    id = Column(String(32), primary_key=True)  # e.g. "soccer"
    name = Column(String(64), nullable=False)
    display_order = Column(Integer, default=0)

    leagues = relationship("League", back_populates="sport")


class League(Base):
    __tablename__ = "leagues"

    id = Column(String(64), primary_key=True)  # e.g. "epl"
    sport_id = Column(String(32), ForeignKey("sports.id"), nullable=False)
    name = Column(String(128), nullable=False)
    country = Column(String(64), default="")
    display_order = Column(Integer, default=0)

    sport = relationship("Sport", back_populates="leagues")
    seasons = relationship("Season", back_populates="league")


class Season(Base):
    __tablename__ = "seasons"

    id = Column(String(64), primary_key=True)  # e.g. "epl_2025_26"
    league_id = Column(String(64), ForeignKey("leagues.id"), nullable=False)
    name = Column(String(64), nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_current = Column(Boolean, default=True)

    league = relationship("League", back_populates="seasons")


class Team(Base):
    __tablename__ = "teams"

    id = Column(String(64), primary_key=True)
    sport_id = Column(String(32), ForeignKey("sports.id"), nullable=False)
    name = Column(String(128), nullable=False)
    short_name = Column(String(32), default="")
    logo_url = Column(String(512), default="")

    __table_args__ = (
        Index("ix_teams_sport", "sport_id"),
    )


class Player(Base):
    __tablename__ = "players"

    id = Column(String(64), primary_key=True)
    team_id = Column(String(64), ForeignKey("teams.id"), nullable=True)
    name = Column(String(128), nullable=False)
    position = Column(String(32), default="")
    jersey_number = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index("ix_players_team", "team_id"),
    )


class Game(Base):
    __tablename__ = "games"

    id = Column(String(64), primary_key=True)
    sport_id = Column(String(32), ForeignKey("sports.id"), nullable=False)
    league_id = Column(String(64), ForeignKey("leagues.id"), nullable=False)
    season_id = Column(String(64), ForeignKey("seasons.id"), nullable=True)
    home_team_id = Column(String(64), ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(String(64), ForeignKey("teams.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    venue = Column(String(256), default="")
    is_playoff = Column(Boolean, default=False)
    status = Column(String(32), default="scheduled")  # scheduled/live/final
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    result_data = Column(JSONB, default=dict)  # period scores, extra stats

    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])

    __table_args__ = (
        Index("ix_games_date", "start_time"),
        Index("ix_games_sport_date", "sport_id", "start_time"),
        Index("ix_games_league", "league_id"),
    )


class TeamGameStats(Base):
    __tablename__ = "team_game_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String(64), ForeignKey("games.id"), nullable=False)
    team_id = Column(String(64), ForeignKey("teams.id"), nullable=False)
    is_home = Column(Boolean, nullable=False)
    stats = Column(JSONB, default=dict)
    # Common stats stored in JSONB:
    # Soccer: goals, shots, sot, corners, fouls, yellows, reds, possession, xg
    # NBA: points, rebounds, assists, steals, blocks, turnovers, fg_pct, ft_pct, three_pct, pace
    # NHL: goals, shots, saves, pp_goals, pp_opps, pim, faceoff_pct
    # Tennis: aces, dfs, first_serve_pct, break_points_won

    __table_args__ = (
        UniqueConstraint("game_id", "team_id", name="uq_team_game_stats"),
        Index("ix_tgs_team", "team_id"),
    )


class PlayerGameStats(Base):
    __tablename__ = "player_game_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String(64), ForeignKey("games.id"), nullable=False)
    player_id = Column(String(64), ForeignKey("players.id"), nullable=False)
    team_id = Column(String(64), ForeignKey("teams.id"), nullable=False)
    minutes = Column(Float, nullable=True)
    started = Column(Boolean, default=False)
    stats = Column(JSONB, default=dict)
    # Common stats stored in JSONB:
    # Soccer: goals, assists, shots, sot, fouls, yellows, reds, key_passes
    # NBA: points, rebounds, assists, steals, blocks, turnovers, threes, fg_made, fg_att, usage_pct
    # NHL: goals, assists, points, sog, toi, pp_points, hits, blocks
    # Tennis: aces, dfs, winners, unforced_errors

    __table_args__ = (
        UniqueConstraint("game_id", "player_id", name="uq_player_game_stats"),
        Index("ix_pgs_player", "player_id"),
        Index("ix_pgs_game", "game_id"),
    )


class OddsSnapshot(Base):
    __tablename__ = "odds_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String(64), ForeignKey("games.id"), nullable=False)
    bookmaker = Column(String(64), nullable=False)
    market_key = Column(String(128), nullable=False)  # normalized key
    outcome_label = Column(String(64), nullable=False)
    line = Column(Float, nullable=True)
    price = Column(Float, nullable=False)  # decimal odds
    implied_prob = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_odds_game", "game_id"),
        Index("ix_odds_market", "market_key"),
        Index("ix_odds_game_market", "game_id", "market_key"),
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String(64), ForeignKey("games.id"), nullable=False)
    market_key = Column(String(128), nullable=False)
    outcome_label = Column(String(64), nullable=False)
    line = Column(Float, nullable=True)
    probability = Column(Float, nullable=False)
    fair_odds = Column(Float, nullable=False)
    edge = Column(Float, nullable=True)
    interval_low = Column(Float, nullable=True)
    interval_high = Column(Float, nullable=True)
    model_version = Column(String(32), default="v1.0")
    factors = Column(JSONB, default=list)  # list of {name, value, description, importance}
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_pred_game", "game_id"),
        Index("ix_pred_market", "market_key"),
        Index("ix_pred_game_market", "game_id", "market_key"),
    )


class Override(Base):
    __tablename__ = "overrides"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String(64), ForeignKey("games.id"), nullable=False)
    override_type = Column(String(32), nullable=False)  # injury/minutes/lineup
    player_id = Column(String(64), nullable=True)
    team_id = Column(String(64), nullable=True)
    key = Column(String(64), nullable=False)
    value = Column(Text, nullable=False)
    note = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)

    __table_args__ = (
        Index("ix_override_game", "game_id"),
    )
