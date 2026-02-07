"""Tests for alerts engine — dedup, cooldown, and 2-signal-type rule."""
import pytest
from datetime import datetime, timedelta

from packages.shared.enums.market import SignalType
from packages.shared.schemas.signals import (
    AdjustedPredictionOut,
    IntelligenceSignalOut,
    NotificationRuleOut,
    NotificationSentOut,
)
from apps.api.services.alerts import evaluate_rule, _compute_dedup_hash


def _make_rule(**kwargs) -> NotificationRuleOut:
    defaults = dict(
        id=1,
        user_key="test-user",
        sports=[],
        leagues=[],
        market_groups=[],
        min_edge=2.0,
        min_confidence=0.0,
        min_prob=0.0,
        quiet_hours={},
        max_alerts_per_game=3,
        max_alerts_per_day=20,
        cooldown_minutes=30,
        enabled=True,
        created_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    return NotificationRuleOut(**defaults)


def _make_prediction(game_id="g1", market_key="moneyline", outcome="Home",
                     adjusted_prob=0.55, edge=5.0) -> AdjustedPredictionOut:
    return AdjustedPredictionOut(
        id=0,
        base_prediction_id=0,
        game_id=game_id,
        market_key=market_key,
        outcome_label=outcome,
        base_prob=0.50,
        adjusted_prob=adjusted_prob,
        adjusted_fair_odds=round(1.0 / adjusted_prob, 3),
        adjusted_edge=edge,
        interval_low=adjusted_prob - 0.05,
        interval_high=adjusted_prob + 0.05,
        applied_signal_ids=["s1", "s2"],
        signal_reasons=[],
        created_at=datetime.utcnow(),
    )


def _make_signal(game_id="g1", sig_type=SignalType.ODDS_MOVE) -> IntelligenceSignalOut:
    import uuid
    return IntelligenceSignalOut(
        id=str(uuid.uuid4()),
        game_id=game_id,
        signal_type=sig_type,
        signal_strength=0.7,
        reliability=0.8,
        headline=f"Test {sig_type.value}",
        description="Test",
        affected_market_groups=["moneyline"],
        affected_periods=["ft"],
        metadata={},
        created_at=datetime.utcnow(),
    )


class TestTwoSignalTypeRequirement:
    """Require at least 2 distinct signal types for an alert."""

    def test_two_types_triggers(self):
        """With 2 different signal types, alert should fire."""
        rule = _make_rule()
        preds = [_make_prediction()]
        signals = [
            _make_signal(sig_type=SignalType.ODDS_MOVE),
            _make_signal(sig_type=SignalType.KEY_PLAYER_OUT),
        ]
        result = evaluate_rule(rule, preds, signals, [])
        assert len(result) == 1

    def test_one_type_blocks(self):
        """With only 1 signal type, no alert should fire."""
        rule = _make_rule()
        preds = [_make_prediction()]
        signals = [
            _make_signal(sig_type=SignalType.ODDS_MOVE),
            _make_signal(sig_type=SignalType.ODDS_MOVE),
        ]
        result = evaluate_rule(rule, preds, signals, [])
        assert len(result) == 0

    def test_zero_signals_blocks(self):
        """With no signals, no alert should fire."""
        rule = _make_rule()
        preds = [_make_prediction()]
        result = evaluate_rule(rule, preds, [], [])
        assert len(result) == 0


class TestDedupHash:
    """Test deduplication logic."""

    def test_same_inputs_same_hash(self):
        h1 = _compute_dedup_hash("g1", "moneyline", None, "Home", 1)
        h2 = _compute_dedup_hash("g1", "moneyline", None, "Home", 1)
        assert h1 == h2

    def test_different_inputs_different_hash(self):
        h1 = _compute_dedup_hash("g1", "moneyline", None, "Home", 1)
        h2 = _compute_dedup_hash("g1", "moneyline", None, "Away", 1)
        assert h1 != h2

    def test_dedup_prevents_repeat(self):
        """Same alert should not be sent twice (dedup hash collision)."""
        rule = _make_rule()
        preds = [_make_prediction()]
        signals = [
            _make_signal(sig_type=SignalType.ODDS_MOVE),
            _make_signal(sig_type=SignalType.KEY_PLAYER_OUT),
        ]
        # First evaluation
        first = evaluate_rule(rule, preds, signals, [])
        assert len(first) == 1

        # Second evaluation with first result in history
        second = evaluate_rule(rule, preds, signals, first)
        assert len(second) == 0


class TestCooldown:
    """Test cooldown enforcement."""

    def test_cooldown_blocks_recent(self):
        """Alert should be blocked if cooldown hasn't elapsed."""
        rule = _make_rule(cooldown_minutes=60)
        preds = [_make_prediction()]
        signals = [
            _make_signal(sig_type=SignalType.ODDS_MOVE),
            _make_signal(sig_type=SignalType.KEY_PLAYER_OUT),
        ]
        recent = NotificationSentOut(
            id=1, rule_id=1, game_id="g_old", market_key="spread",
            selection="Away", edge_pct=3.0, model_prob=0.55, fair_odds=1.82,
            signals_summary=[], payload={},
            sent_at=datetime.utcnow() - timedelta(minutes=10),
            dedup_hash="old_hash",
        )
        result = evaluate_rule(rule, preds, signals, [recent])
        assert len(result) == 0

    def test_cooldown_allows_old(self):
        """Alert should pass if cooldown has elapsed."""
        rule = _make_rule(cooldown_minutes=30)
        preds = [_make_prediction()]
        signals = [
            _make_signal(sig_type=SignalType.ODDS_MOVE),
            _make_signal(sig_type=SignalType.KEY_PLAYER_OUT),
        ]
        old = NotificationSentOut(
            id=1, rule_id=1, game_id="g_old", market_key="spread",
            selection="Away", edge_pct=3.0, model_prob=0.55, fair_odds=1.82,
            signals_summary=[], payload={},
            sent_at=datetime.utcnow() - timedelta(minutes=60),
            dedup_hash="old_hash",
        )
        result = evaluate_rule(rule, preds, signals, [old])
        assert len(result) == 1


class TestDailyCap:
    """Test daily alert cap."""

    def test_daily_cap_blocks(self):
        """Should block when daily cap exceeded."""
        rule = _make_rule(max_alerts_per_day=2)
        preds = [_make_prediction()]
        signals = [
            _make_signal(sig_type=SignalType.ODDS_MOVE),
            _make_signal(sig_type=SignalType.KEY_PLAYER_OUT),
        ]
        today = datetime.utcnow()
        history = [
            NotificationSentOut(
                id=i, rule_id=1, game_id=f"g{i}", market_key="ml",
                selection="Home", edge_pct=3.0, model_prob=0.55, fair_odds=1.82,
                signals_summary=[], payload={},
                sent_at=today - timedelta(minutes=i * 5),
                dedup_hash=f"hash_{i}",
            )
            for i in range(2)
        ]
        result = evaluate_rule(rule, preds, signals, history)
        assert len(result) == 0


class TestDisabledRule:
    """Test disabled rule."""

    def test_disabled_rule_no_alerts(self):
        rule = _make_rule(enabled=False)
        preds = [_make_prediction()]
        signals = [
            _make_signal(sig_type=SignalType.ODDS_MOVE),
            _make_signal(sig_type=SignalType.KEY_PLAYER_OUT),
        ]
        result = evaluate_rule(rule, preds, signals, [])
        assert len(result) == 0


class TestMinEdge:
    """Test minimum edge filter."""

    def test_below_min_edge_filtered(self):
        rule = _make_rule(min_edge=10.0)
        preds = [_make_prediction(edge=5.0)]
        signals = [
            _make_signal(sig_type=SignalType.ODDS_MOVE),
            _make_signal(sig_type=SignalType.KEY_PLAYER_OUT),
        ]
        result = evaluate_rule(rule, preds, signals, [])
        assert len(result) == 0

    def test_above_min_edge_passes(self):
        rule = _make_rule(min_edge=3.0)
        preds = [_make_prediction(edge=5.0)]
        signals = [
            _make_signal(sig_type=SignalType.ODDS_MOVE),
            _make_signal(sig_type=SignalType.KEY_PLAYER_OUT),
        ]
        result = evaluate_rule(rule, preds, signals, [])
        assert len(result) == 1
