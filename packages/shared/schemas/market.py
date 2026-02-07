from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from packages.shared.enums.market import (
    BetTag, CorrelationCategory, LineUnit, MarketGroup, MarketType,
    OutcomeType, Period, RiskLevel, Side,
)
from packages.shared.enums.sport import League, Sport


class MarketSpec(BaseModel):
    """Specifies a particular market line."""
    market_group: MarketGroup
    market_type: MarketType
    period: Period = Period.FULL_TIME
    side: Side = Side.TOTAL
    line_value: float | None = None
    line_unit: LineUnit | None = None
    player_id: str | None = None
    bucket_label: str | None = None

    @property
    def normalized_key(self) -> str:
        parts = [self.market_group.value, self.period.value, self.side.value]
        if self.line_value is not None:
            parts.append(str(self.line_value))
        if self.player_id:
            parts.append(self.player_id)
        if self.bucket_label:
            parts.append(self.bucket_label)
        return ":".join(parts)


class MarketOutcome(BaseModel):
    """One selectable outcome within a market."""
    outcome_type: OutcomeType
    label: str
    score_home: int | None = None
    score_away: int | None = None
    bucket_low: float | None = None
    bucket_high: float | None = None


class MarketDefinition(BaseModel):
    """Full definition of a market available in the catalog."""
    market_group: MarketGroup
    market_type: MarketType
    sport: Sport
    display_name: str
    description: str = ""
    supported_periods: list[Period] = Field(default_factory=lambda: [Period.FULL_TIME])
    supported_sides: list[Side] = Field(default_factory=lambda: [Side.TOTAL])
    line_unit: LineUnit | None = None
    default_lines: list[float] = Field(default_factory=list)
    outcomes: list[MarketOutcome] = Field(default_factory=list)
    correlation_categories: list[CorrelationCategory] = Field(default_factory=list)
    requires_player: bool = False
    model_family: str = "logistic"


class BookmakerMapping(BaseModel):
    """Maps bookmaker-specific market names to normalized keys."""
    bookmaker: str
    bookmaker_market_name: str
    normalized_market_group: MarketGroup
    period: Period = Period.FULL_TIME
    side: Side = Side.TOTAL
    outcome_map: dict[str, OutcomeType] = Field(default_factory=dict)


class ExplanationFactor(BaseModel):
    """One factor in the model explanation."""
    name: str
    value: float
    description: str
    importance: float = 0.0


class PredictionResult(BaseModel):
    """Prediction for one specific market outcome."""
    game_id: str
    market_spec: MarketSpec
    outcome: OutcomeType
    outcome_label: str
    probability: float = Field(ge=0.0, le=1.0)
    fair_odds: float = Field(ge=1.0)
    interval_low: float = Field(ge=0.0, le=1.0)
    interval_high: float = Field(ge=0.0, le=1.0)
    model_version: str = "v1.0"
    factors: list[ExplanationFactor] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BestBet(BaseModel):
    """A value bet recommendation."""
    game_id: str
    sport: Sport
    league: League
    home_team: str
    away_team: str
    start_time: datetime
    market_name: str
    market_spec: MarketSpec
    outcome: OutcomeType
    outcome_label: str
    bookmaker_odds: float
    implied_prob: float
    model_prob: float
    fair_odds: float
    edge_pct: float
    interval_low: float
    interval_high: float
    factors: list[ExplanationFactor] = Field(default_factory=list)
    risk_note: str = ""
    risk_level: RiskLevel = RiskLevel.MEDIUM
    tag: BetTag = BetTag.VALUE


class BetBuilderLeg(BaseModel):
    """One leg in a bet builder combo."""
    market_spec: MarketSpec
    outcome: OutcomeType
    outcome_label: str
    individual_prob: float
    individual_fair_odds: float
    correlation_categories: list[CorrelationCategory] = Field(default_factory=list)


class BetBuilderProposal(BaseModel):
    """A suggested bet builder combination."""
    game_id: str
    legs: list[BetBuilderLeg]
    naive_combined_prob: float
    correlation_adjustment: float
    adjusted_prob: float
    adjusted_fair_odds: float
    bookmaker_combo_odds: float | None = None
    edge_pct: float | None = None
    risk_level: RiskLevel = RiskLevel.HIGH
    compatible: bool = True
    incompatibility_reason: str | None = None


class BacktestMetrics(BaseModel):
    """Metrics from a backtest run."""
    total_bets: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    roi_pct: float = 0.0
    log_loss: float | None = None
    brier_score: float | None = None
    calibration_error: float | None = None
    max_drawdown: float = 0.0
    avg_edge: float = 0.0
    sharpe_ratio: float | None = None


class BacktestReport(BaseModel):
    """Full backtest report."""
    sport: Sport
    league: League
    market_group: MarketGroup
    period_start: datetime
    period_end: datetime
    model_version: str
    flat_stake: BacktestMetrics = Field(default_factory=BacktestMetrics)
    kelly_stake: BacktestMetrics | None = None
    sample_size: int = 0
    notes: str = ""
    generated_at: datetime = Field(default_factory=datetime.utcnow)
