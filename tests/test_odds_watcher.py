"""Tests for odds watcher — move detection thresholds."""
import pytest
from datetime import datetime

from packages.shared.schemas.game import OddsSnapshot
from apps.api.services.odds_watcher import detect_odds_moves, detect_line_injuries


class TestDetectOddsMoves:
    """Test odds move detection with various scenarios."""

    def _make_snap(self, game_id, market_key, outcome, price, ts_offset_min=0, line=None, bookmaker="bet365"):
        return OddsSnapshot(
            game_id=game_id,
            bookmaker=bookmaker,
            market_key=market_key,
            outcome_label=outcome,
            line=line,
            price=price,
            timestamp=datetime(2026, 2, 8, 10, 0, 0).replace(
                minute=ts_offset_min % 60,
                hour=10 + ts_offset_min // 60,
            ),
        )

    def test_significant_move_detected(self):
        """Move of 7.9pp (2.10 -> 1.80) should be detected."""
        snaps = [
            self._make_snap("g1", "1x2", "Home", 2.10, ts_offset_min=0),
            self._make_snap("g1", "1x2", "Home", 1.80, ts_offset_min=90),
        ]
        moves, signals = detect_odds_moves(snaps)
        assert len(moves) == 1
        assert len(signals) == 1
        assert moves[0].game_id == "g1"
        assert abs(moves[0].delta_implied_prob) >= 0.03
        assert signals[0].signal_type.value == "odds_move"

    def test_small_move_ignored(self):
        """Move of ~1pp should NOT be detected."""
        snaps = [
            self._make_snap("g1", "1x2", "Home", 2.00, ts_offset_min=0),
            self._make_snap("g1", "1x2", "Home", 1.97, ts_offset_min=90),
        ]
        moves, signals = detect_odds_moves(snaps)
        assert len(moves) == 0
        assert len(signals) == 0

    def test_line_change_detected(self):
        """Line change from -3.5 to -4.5 should be detected even with same price."""
        snaps = [
            self._make_snap("g1", "spread", "Home", 1.91, ts_offset_min=0, line=-3.5),
            self._make_snap("g1", "spread", "Home", 1.91, ts_offset_min=90, line=-4.5),
        ]
        moves, signals = detect_odds_moves(snaps)
        assert len(moves) == 1
        assert moves[0].old_line == -3.5
        assert moves[0].new_line == -4.5

    def test_single_snapshot_no_move(self):
        """Single snapshot cannot produce a move."""
        snaps = [
            self._make_snap("g1", "1x2", "Home", 2.10, ts_offset_min=0),
        ]
        moves, signals = detect_odds_moves(snaps)
        assert len(moves) == 0
        assert len(signals) == 0

    def test_signal_strength_proportional(self):
        """Larger moves should produce stronger signals."""
        snaps_big = [
            self._make_snap("g1", "1x2", "Home", 2.50, ts_offset_min=0),
            self._make_snap("g1", "1x2", "Home", 1.80, ts_offset_min=90),
        ]
        snaps_small = [
            self._make_snap("g2", "1x2", "Home", 2.10, ts_offset_min=0),
            self._make_snap("g2", "1x2", "Home", 1.95, ts_offset_min=90),
        ]
        _, sigs_big = detect_odds_moves(snaps_big)
        _, sigs_small = detect_odds_moves(snaps_small)
        assert len(sigs_big) == 1
        assert len(sigs_small) == 1
        assert sigs_big[0].signal_strength > sigs_small[0].signal_strength

    def test_multiple_games(self):
        """Moves from different games detected independently."""
        snaps = [
            self._make_snap("g1", "1x2", "Home", 2.10, ts_offset_min=0),
            self._make_snap("g1", "1x2", "Home", 1.70, ts_offset_min=90),
            self._make_snap("g2", "ml", "Away", 3.00, ts_offset_min=0),
            self._make_snap("g2", "ml", "Away", 2.20, ts_offset_min=90),
        ]
        moves, signals = detect_odds_moves(snaps)
        assert len(moves) == 2
        game_ids = {m.game_id for m in moves}
        assert game_ids == {"g1", "g2"}


class TestDetectLineInjuries:
    """Test injury/lineup signal generation."""

    def test_injury_out_signal(self):
        overrides = [
            {"override_type": "injury", "player_id": "p1", "team_id": "t1",
             "key": "Star Player", "value": "out", "note": "ACL tear"}
        ]
        signals = detect_line_injuries(overrides, "game1")
        assert len(signals) == 1
        assert signals[0].signal_type.value == "key_player_out"
        assert signals[0].signal_strength == 0.8

    def test_injury_doubtful_signal(self):
        overrides = [
            {"override_type": "injury", "player_id": "p1", "team_id": "t1",
             "key": "Player X", "value": "doubtful", "note": "Minor knock"}
        ]
        signals = detect_line_injuries(overrides, "game1")
        assert len(signals) == 1
        assert signals[0].signal_strength == 0.5

    def test_lineup_confirmed_signal(self):
        overrides = [
            {"override_type": "lineup", "player_id": None, "team_id": "t1",
             "key": "Starting XI", "value": "Confirmed", "note": "Full strength"}
        ]
        signals = detect_line_injuries(overrides, "game1")
        assert len(signals) == 1
        assert signals[0].signal_type.value == "lineup_confirmed"

    def test_irrelevant_override_ignored(self):
        overrides = [
            {"override_type": "minutes", "player_id": "p1", "team_id": "t1",
             "key": "minutes_cap", "value": "25", "note": "Returning from injury"}
        ]
        signals = detect_line_injuries(overrides, "game1")
        assert len(signals) == 0

    def test_injury_probable_ignored(self):
        overrides = [
            {"override_type": "injury", "player_id": "p1", "team_id": "t1",
             "key": "Player", "value": "probable", "note": "Should play"}
        ]
        signals = detect_line_injuries(overrides, "game1")
        assert len(signals) == 0
