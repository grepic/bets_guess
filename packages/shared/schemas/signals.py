"""Schemas for intelligence signals, notifications, and segment profiles."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from packages.shared.enums.market import MarketGroup, Period, SignalType, RiskLevel


# ────────────────────────────────────────────────────────────
# Intelligence Signals
# ────────────────────────────────────────────────────────────

class IntelligenceSignalOut(BaseModel):
    """An intelligence signal detected by the system."""
    id: str
    sport_id: str | None = None
    league_id: str | None = None
    game_id: str | None = None
    team_id: str | None = None
    player_id: str | None = None
    signal_type: SignalType
    signal_strength: float = Field(ge=0.0, le=1.0)
    reliability: float = Field(ge=0.0, le=1.0)
    headline: str = ""
    description: str = ""
    affected_market_groups: list[str] = Field(default_factory=list)
    affected_periods: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ────────────────────────────────────────────────────────────
# Notification Rules
# ────────────────────────────────────────────────────────────

class NotificationRuleIn(BaseModel):
    """Input schema for creating/updating a notification rule."""
    user_key: str
    sports: list[str] = Field(default_factory=list)
    leagues: list[str] = Field(default_factory=list)
    market_groups: list[str] = Field(default_factory=list)
    min_edge: float = 3.0
    min_confidence: float = 0.0
    min_prob: float = 0.0
    quiet_hours: dict = Field(default_factory=dict)  # {"start": "23:00", "end": "07:00"}
    max_alerts_per_game: int = 3
    max_alerts_per_day: int = 20
    cooldown_minutes: int = 30
    enabled: bool = True


class NotificationRuleOut(BaseModel):
    """Output schema for a notification rule."""
    id: int
    user_key: str
    sports: list[str] = Field(default_factory=list)
    leagues: list[str] = Field(default_factory=list)
    market_groups: list[str] = Field(default_factory=list)
    min_edge: float = 3.0
    min_confidence: float = 0.0
    min_prob: float = 0.0
    quiet_hours: dict = Field(default_factory=dict)
    max_alerts_per_game: int = 3
    max_alerts_per_day: int = 20
    cooldown_minutes: int = 30
    enabled: bool = True
    created_at: datetime | None = None


class NotificationSentOut(BaseModel):
    """A notification that was sent."""
    model_config = {"protected_namespaces": ()}
    id: int
    rule_id: int
    game_id: str
    market_key: str
    line: float | None = None
    selection: str = ""
    edge_pct: float = 0.0
    model_prob: float = 0.0
    fair_odds: float = 0.0
    signals_summary: list[dict] = Field(default_factory=list)
    payload: dict = Field(default_factory=dict)
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    dedup_hash: str = ""


# ────────────────────────────────────────────────────────────
# Segment Profiles
# ────────────────────────────────────────────────────────────

class TeamSegmentProfileOut(BaseModel):
    """Per-period team performance profile."""
    id: int
    team_id: str
    segment_period: str
    offensive_rating: float = 0.0
    defensive_rating: float = 0.0
    net_rating: float = 0.0
    volatility: float = 0.0
    clutch_factor: float = 0.0
    sample_size: int = 0
    updated_at: datetime | None = None


class MatchupSegmentProfileOut(BaseModel):
    """Head-to-head segment-level analysis."""
    id: int
    team_a_id: str
    team_b_id: str
    segment_period: str
    adjusted_edge_pp: float = 0.0
    h2h_weighted_effect_pp: float = 0.0
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    style_tags: list[str] = Field(default_factory=list)
    sample_size: int = 0
    updated_at: datetime | None = None


# ────────────────────────────────────────────────────────────
# Adjusted Prediction
# ────────────────────────────────────────────────────────────

class AdjustedPredictionOut(BaseModel):
    """A prediction adjusted by intelligence signals."""
    id: int
    base_prediction_id: int
    game_id: str
    market_key: str
    outcome_label: str
    base_prob: float
    adjusted_prob: float
    adjusted_fair_odds: float
    adjusted_edge: float | None = None
    interval_low: float
    interval_high: float
    applied_signal_ids: list[str] = Field(default_factory=list)
    signal_reasons: list[dict] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ────────────────────────────────────────────────────────────
# Odds Move
# ────────────────────────────────────────────────────────────

class OddsMoveOut(BaseModel):
    """A significant odds movement."""
    game_id: str
    bookmaker: str
    market_key: str
    outcome_label: str
    old_price: float
    new_price: float
    old_implied_prob: float
    new_implied_prob: float
    delta_implied_prob: float
    old_line: float | None = None
    new_line: float | None = None
    detected_at: datetime = Field(default_factory=datetime.utcnow)
