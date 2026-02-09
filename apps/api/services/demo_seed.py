"""Demo seed — populate in-memory stores with fixture-derived signals and moves."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from packages.shared.schemas.game import OddsSnapshot
from packages.shared.schemas.signals import (
    AdjustedPredictionOut,
    IntelligenceSignalOut,
    OddsMoveOut,
)
from apps.api.services.odds_watcher import detect_odds_moves, detect_line_injuries
from apps.api.services.segment_profiles import (
    compute_matchup_segment_profiles,
    compute_team_segment_profiles,
    generate_segment_signals,
)
from apps.api.services.signal_adjuster import adjust_prediction

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "packages" / "fixtures"


def _load_json(subdir: str, filename: str) -> list | dict:
    path = FIXTURES_DIR / subdir / filename
    if path.exists():
        return json.loads(path.read_text())
    return []


def seed_demo_data() -> dict:
    """Run all services on fixture data and return populated stores.

    Returns dict with keys: signals, moves, adjusted_predictions
    """
    all_signals: list[IntelligenceSignalOut] = []
    all_moves: list[OddsMoveOut] = []
    all_adjusted: list[AdjustedPredictionOut] = []

    # ── 1. Odds moves from fixture snapshots ──
    raw_snaps = _load_json("signals", "odds_snapshots.json")
    if raw_snaps:
        snapshots = [
            OddsSnapshot(
                game_id=s["game_id"],
                bookmaker=s["bookmaker"],
                market_key=s["market_key"],
                outcome_label=s["outcome_label"],
                line=s.get("line"),
                price=s["price"],
                implied_prob=s.get("implied_prob"),
                timestamp=datetime.fromisoformat(s["timestamp"]),
            )
            for s in raw_snaps
        ]
        moves, move_signals = detect_odds_moves(snapshots)
        all_moves.extend(moves)
        all_signals.extend(move_signals)

    # ── 2. Injury/lineup signals from overrides ──
    raw_overrides = _load_json("signals", "overrides.json")
    if raw_overrides:
        # Group overrides by game_id
        by_game: dict[str, list[dict]] = {}
        for ovr in raw_overrides:
            by_game.setdefault(ovr["game_id"], []).append(ovr)
        for game_id, overrides in by_game.items():
            injury_signals = detect_line_injuries(overrides, game_id)
            all_signals.extend(injury_signals)

    # ── 3. Segment profiles + signals ──
    raw_segments = _load_json("signals", "segment_stats.json")
    if raw_segments and isinstance(raw_segments, dict):
        # Process known matchups from odds fixtures
        matchup_pairs = [
            ("arsenal", "chelsea", "soc_ars_che_20260208"),
            ("lakers", "celtics", "nba_lal_bos_20260208"),
        ]
        for team_a, team_b, game_id in matchup_pairs:
            stats_a = raw_segments.get(team_a, [])
            stats_b = raw_segments.get(team_b, [])
            if not stats_a or not stats_b:
                continue

            profiles_a = compute_team_segment_profiles(team_a, stats_a)
            profiles_b = compute_team_segment_profiles(team_b, stats_b)
            matchup_profiles = compute_matchup_segment_profiles(
                team_a, team_b, profiles_a, profiles_b,
            )
            seg_signals = generate_segment_signals(
                team_a, team_b, game_id, matchup_profiles, profiles_a, profiles_b,
            )
            all_signals.extend(seg_signals)

    # ── 4. Generate demo adjusted predictions ──
    # Create some base predictions and adjust them with the signals we found
    demo_predictions = [
        {"id": 1, "game_id": "soc_ars_che_20260208", "market_key": "soccer_1x2_ft",
         "outcome_label": "Home", "probability": 0.48, "interval_low": 0.42, "interval_high": 0.54},
        {"id": 2, "game_id": "soc_ars_che_20260208", "market_key": "soccer_1x2_ft",
         "outcome_label": "Draw", "probability": 0.28, "interval_low": 0.22, "interval_high": 0.34},
        {"id": 3, "game_id": "soc_ars_che_20260208", "market_key": "soccer_1x2_ft",
         "outcome_label": "Away", "probability": 0.24, "interval_low": 0.18, "interval_high": 0.30},
        {"id": 4, "game_id": "soc_ars_che_20260208", "market_key": "totals",
         "outcome_label": "Over 2.5", "probability": 0.55, "interval_low": 0.49, "interval_high": 0.61},
        {"id": 5, "game_id": "nba_lal_bos_20260208", "market_key": "nba_spread",
         "outcome_label": "Home", "probability": 0.47, "interval_low": 0.41, "interval_high": 0.53},
        {"id": 6, "game_id": "nba_lal_bos_20260208", "market_key": "nba_totals",
         "outcome_label": "Over 220.5", "probability": 0.52, "interval_low": 0.46, "interval_high": 0.58},
        {"id": 7, "game_id": "nba_lal_bos_20260208", "market_key": "moneyline",
         "outcome_label": "Home", "probability": 0.44, "interval_low": 0.38, "interval_high": 0.50},
    ]

    bookmaker_odds = {
        "soccer_1x2_ft:Home": 1.80,
        "soccer_1x2_ft:Draw": 3.50,
        "soccer_1x2_ft:Away": 4.20,
        "totals:Over 2.5": 1.85,
        "nba_spread:Home": 1.91,
        "nba_totals:Over 220.5": 1.87,
        "moneyline:Home": 2.30,
    }

    for pred in demo_predictions:
        game_signals = [s for s in all_signals if s.game_id == pred["game_id"]]
        odds_key = f"{pred['market_key']}:{pred['outcome_label']}"
        book_odds = bookmaker_odds.get(odds_key)

        adjusted = adjust_prediction(
            base_prediction_id=pred["id"],
            game_id=pred["game_id"],
            market_key=pred["market_key"],
            outcome_label=pred["outcome_label"],
            base_prob=pred["probability"],
            interval_low=pred["interval_low"],
            interval_high=pred["interval_high"],
            signals=game_signals,
            bookmaker_odds=book_odds,
        )
        all_adjusted.append(adjusted)

    return {
        "signals": all_signals,
        "moves": all_moves,
        "adjusted_predictions": all_adjusted,
    }
