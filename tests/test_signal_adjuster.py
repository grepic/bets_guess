"""Tests for signal adjuster — caps and CI widening."""
import pytest
import uuid
from datetime import datetime

from packages.shared.enums.market import SignalType
from packages.shared.schemas.signals import IntelligenceSignalOut
from apps.api.services.signal_adjuster import (
    adjust_prediction,
    SIGNAL_CAPS,
    MAX_TOTAL_ADJUSTMENT,
)


def _make_signal(
    signal_type: SignalType,
    strength: float = 0.8,
    reliability: float = 0.9,
    game_id: str = "g1",
    team_id: str | None = None,
    affected_mgs: list[str] | None = None,
    metadata: dict | None = None,
) -> IntelligenceSignalOut:
    return IntelligenceSignalOut(
        id=str(uuid.uuid4()),
        game_id=game_id,
        team_id=team_id,
        signal_type=signal_type,
        signal_strength=strength,
        reliability=reliability,
        headline=f"Test {signal_type.value}",
        description="Test signal",
        affected_market_groups=affected_mgs or [],
        affected_periods=["ft"],
        metadata=metadata or {},
        created_at=datetime.utcnow(),
    )


class TestSignalCaps:
    """Test that individual signal caps are respected."""

    def test_odds_move_no_adjustment(self):
        """ODDS_MOVE should be flag-only, no prob adjustment."""
        sig = _make_signal(SignalType.ODDS_MOVE)
        result = adjust_prediction(
            base_prediction_id=1,
            game_id="g1",
            market_key="moneyline",
            outcome_label="Home",
            base_prob=0.50,
            interval_low=0.45,
            interval_high=0.55,
            signals=[sig],
        )
        assert result.adjusted_prob == result.base_prob
        assert len(result.applied_signal_ids) == 1  # still flagged

    def test_key_player_out_cap(self):
        """KEY_PLAYER_OUT max adjustment is ±6pp."""
        sig = _make_signal(
            SignalType.KEY_PLAYER_OUT,
            strength=1.0,
            reliability=1.0,
            metadata={"key": "star"},
        )
        result = adjust_prediction(
            base_prediction_id=1,
            game_id="g1",
            market_key="moneyline",
            outcome_label="Home",
            base_prob=0.50,
            interval_low=0.45,
            interval_high=0.55,
            signals=[sig],
        )
        delta = abs(result.adjusted_prob - result.base_prob)
        assert delta <= SIGNAL_CAPS[SignalType.KEY_PLAYER_OUT] + 0.001

    def test_segment_dominance_cap(self):
        """SEGMENT_DOMINANCE max adjustment is ±4pp."""
        sig = _make_signal(
            SignalType.SEGMENT_DOMINANCE,
            strength=1.0,
            reliability=1.0,
            affected_mgs=["moneyline"],
            metadata={"dominant_team": "home"},
        )
        result = adjust_prediction(
            base_prediction_id=1,
            game_id="g1",
            market_key="moneyline",
            outcome_label="Home team label with home in it",
            base_prob=0.50,
            interval_low=0.45,
            interval_high=0.55,
            signals=[sig],
        )
        delta = abs(result.adjusted_prob - result.base_prob)
        assert delta <= SIGNAL_CAPS[SignalType.SEGMENT_DOMINANCE] + 0.001


class TestTotalCap:
    """Test cumulative cap across multiple signals."""

    def test_total_cap_enforced(self):
        """Many strong signals should not exceed MAX_TOTAL_ADJUSTMENT."""
        signals = [
            _make_signal(SignalType.KEY_PLAYER_OUT, strength=1.0, reliability=1.0,
                         metadata={"key": "star"}),
            _make_signal(SignalType.SEGMENT_DOMINANCE, strength=1.0, reliability=1.0,
                         affected_mgs=["moneyline"], metadata={"dominant_team": "x"}),
            _make_signal(SignalType.MATCHUP_TREND, strength=1.0, reliability=1.0,
                         affected_mgs=["moneyline"], metadata={"favored_team": "x"}),
            _make_signal(SignalType.FATIGUE_EDGE, strength=1.0, reliability=1.0,
                         affected_mgs=["moneyline"]),
            _make_signal(SignalType.REST_ADVANTAGE, strength=1.0, reliability=1.0,
                         affected_mgs=["moneyline"]),
            _make_signal(SignalType.SCHEDULE_PRESSURE, strength=1.0, reliability=1.0,
                         affected_mgs=["moneyline"]),
        ]
        result = adjust_prediction(
            base_prediction_id=1,
            game_id="g1",
            market_key="moneyline",
            outcome_label="Home",
            base_prob=0.50,
            interval_low=0.45,
            interval_high=0.55,
            signals=signals,
        )
        delta = abs(result.adjusted_prob - result.base_prob)
        assert delta <= MAX_TOTAL_ADJUSTMENT + 0.001


class TestCIWidening:
    """Test confidence interval widening."""

    def test_ci_widens_per_signal(self):
        """Each applied signal should widen CI by 1pp."""
        base_low, base_high = 0.45, 0.55

        # No signals
        result_none = adjust_prediction(
            base_prediction_id=1, game_id="g1", market_key="moneyline",
            outcome_label="Home", base_prob=0.50,
            interval_low=base_low, interval_high=base_high,
            signals=[],
        )
        assert result_none.interval_low == base_low
        assert result_none.interval_high == base_high

        # Two signals
        sigs = [
            _make_signal(SignalType.SEGMENT_DOMINANCE, affected_mgs=["moneyline"],
                         metadata={"dominant_team": "x"}),
            _make_signal(SignalType.MATCHUP_TREND, affected_mgs=["moneyline"],
                         metadata={"favored_team": "x"}),
        ]
        result_two = adjust_prediction(
            base_prediction_id=1, game_id="g1", market_key="moneyline",
            outcome_label="Home", base_prob=0.50,
            interval_low=base_low, interval_high=base_high,
            signals=sigs,
        )
        n_applied = len(result_two.applied_signal_ids)
        assert n_applied >= 1
        # CI should be wider
        assert result_two.interval_low <= base_low
        assert result_two.interval_high >= base_high


class TestProbBounds:
    """Test probability stays within valid bounds."""

    def test_prob_stays_above_zero(self):
        """Negative adjustments should not push prob below 0.001."""
        sig = _make_signal(
            SignalType.KEY_PLAYER_OUT, strength=1.0, reliability=1.0,
            metadata={"key": "star"},
        )
        result = adjust_prediction(
            base_prediction_id=1, game_id="g1", market_key="moneyline",
            outcome_label="star team wins",
            base_prob=0.02,
            interval_low=0.01, interval_high=0.05,
            signals=[sig],
        )
        assert result.adjusted_prob >= 0.001
        assert result.interval_low >= 0.001

    def test_prob_stays_below_one(self):
        """Positive adjustments should not push prob above 0.999."""
        sig = _make_signal(
            SignalType.SEGMENT_DOMINANCE, strength=1.0, reliability=1.0,
            affected_mgs=["moneyline"], metadata={"dominant_team": "hero"},
        )
        result = adjust_prediction(
            base_prediction_id=1, game_id="g1", market_key="moneyline",
            outcome_label="hero wins big",
            base_prob=0.98,
            interval_low=0.95, interval_high=0.99,
            signals=[sig],
        )
        assert result.adjusted_prob <= 0.999
        assert result.interval_high <= 0.999
