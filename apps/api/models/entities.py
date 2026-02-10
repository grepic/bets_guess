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


# ────────────────────────────────────────────────────────────
# Intelligence Signals layer (upgrade)
# ────────────────────────────────────────────────────────────

class IntelligenceSignal(Base):
    __tablename__ = "intelligence_signals"

    id = Column(String(64), primary_key=True)  # uuid
    sport_id = Column(String(32), nullable=True)
    league_id = Column(String(64), nullable=True)
    game_id = Column(String(64), nullable=True)
    team_id = Column(String(64), nullable=True)
    player_id = Column(String(64), nullable=True)
    signal_type = Column(String(32), nullable=False)  # SignalType enum value
    signal_strength = Column(Float, nullable=False, default=0.5)
    reliability = Column(Float, nullable=False, default=0.5)
    headline = Column(String(256), default="")
    description = Column(Text, default="")
    affected_market_groups = Column(JSONB, default=list)
    affected_periods = Column(JSONB, default=list)
    signal_metadata = Column("metadata", JSONB, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_signal_game", "game_id"),
        Index("ix_signal_type", "signal_type"),
        Index("ix_signal_created", "created_at"),
        Index("ix_signal_game_type", "game_id", "signal_type"),
    )


class TeamSegmentProfile(Base):
    __tablename__ = "team_segment_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(String(64), nullable=False)
    segment_period = Column(String(16), nullable=False)  # Period enum value
    offensive_rating = Column(Float, default=0.0)
    defensive_rating = Column(Float, default=0.0)
    net_rating = Column(Float, default=0.0)
    volatility = Column(Float, default=0.0)
    clutch_factor = Column(Float, default=0.0)
    sample_size = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("team_id", "segment_period", name="uq_team_segment"),
        Index("ix_tsp_team", "team_id"),
    )


class MatchupSegmentProfile(Base):
    __tablename__ = "matchup_segment_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_a_id = Column(String(64), nullable=False)
    team_b_id = Column(String(64), nullable=False)
    segment_period = Column(String(16), nullable=False)
    adjusted_edge_pp = Column(Float, default=0.0)
    h2h_weighted_effect_pp = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    style_tags = Column(JSONB, default=list)
    sample_size = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("team_a_id", "team_b_id", "segment_period", name="uq_matchup_segment"),
        Index("ix_msp_teams", "team_a_id", "team_b_id"),
    )


class AdjustedPrediction(Base):
    __tablename__ = "adjusted_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    base_prediction_id = Column(Integer, nullable=True)
    game_id = Column(String(64), nullable=False)
    market_key = Column(String(128), nullable=False)
    outcome_label = Column(String(64), nullable=False)
    base_prob = Column(Float, nullable=False)
    adjusted_prob = Column(Float, nullable=False)
    adjusted_fair_odds = Column(Float, nullable=False)
    adjusted_edge = Column(Float, nullable=True)
    interval_low = Column(Float, nullable=True)
    interval_high = Column(Float, nullable=True)
    applied_signal_ids = Column(JSONB, default=list)
    signal_reasons = Column(JSONB, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_apred_game", "game_id"),
        Index("ix_apred_game_market", "game_id", "market_key"),
    )


class NotificationRule(Base):
    __tablename__ = "notification_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_key = Column(String(128), nullable=False)
    sports = Column(JSONB, default=list)
    leagues = Column(JSONB, default=list)
    market_groups = Column(JSONB, default=list)
    min_edge = Column(Float, default=3.0)
    min_confidence = Column(Float, default=0.0)
    min_prob = Column(Float, default=0.0)
    quiet_hours = Column(JSONB, default=dict)
    max_alerts_per_game = Column(Integer, default=3)
    max_alerts_per_day = Column(Integer, default=20)
    cooldown_minutes = Column(Integer, default=30)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_nrule_user", "user_key"),
    )


class NotificationSent(Base):
    __tablename__ = "notifications_sent"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey("notification_rules.id"), nullable=False)
    game_id = Column(String(64), nullable=False)
    market_key = Column(String(128), nullable=False)
    line = Column(Float, nullable=True)
    selection = Column(String(64), default="")
    edge_pct = Column(Float, default=0.0)
    model_prob = Column(Float, default=0.0)
    fair_odds = Column(Float, default=0.0)
    signals_summary = Column(JSONB, default=list)
    payload = Column(JSONB, default=dict)
    sent_at = Column(DateTime, default=datetime.utcnow)
    dedup_hash = Column(String(64), nullable=False)

    __table_args__ = (
        Index("ix_nsent_rule", "rule_id"),
        Index("ix_nsent_dedup", "dedup_hash"),
        Index("ix_nsent_game", "game_id"),
        Index("ix_nsent_sent", "sent_at"),
    )
