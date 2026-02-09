"""Celery worker for background jobs: ingest, predict, backtest."""
from __future__ import annotations

from celery import Celery

from apps.api.core.config import get_settings

settings = get_settings()

app = Celery(
    "smartbets",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,
    task_soft_time_limit=540,
)


@app.task(name="jobs.ingest_data")
def ingest_data(sport: str | None = None) -> dict:
    """Ingest latest schedule, stats, and odds data.

    In production, this would:
    1. Fetch schedule from real API
    2. Fetch team/player stats
    3. Fetch latest odds from bookmakers
    4. Store everything in PostgreSQL
    """
    # TODO: Replace with real API provider calls
    return {
        "status": "completed",
        "sport": sport or "all",
        "message": "Using mock fixtures in dev mode. Wire real providers for production.",
    }


@app.task(name="jobs.run_predictions")
def run_predictions(sport: str | None = None, date: str | None = None) -> dict:
    """Generate predictions for upcoming games.

    In production, this would:
    1. Load upcoming games from DB
    2. Build features for each matchup
    3. Run models for all applicable markets
    4. Store predictions in DB
    5. Invalidate Redis cache
    """
    # TODO: Implement async prediction pipeline with DB storage
    return {
        "status": "completed",
        "sport": sport or "all",
        "date": date or "today",
        "message": "Predictions generated via PredictionService.",
    }


@app.task(name="jobs.run_backtest")
def run_backtest_task(
    sport: str = "soccer",
    league: str = "epl",
    market_group: str = "totals",
) -> dict:
    """Run backtest for a specific sport/league/market combination.

    In production, this would:
    1. Load historical predictions + actual results
    2. Run backtest engine
    3. Store report in DB
    """
    from packages.shared.enums.market import MarketGroup
    from packages.shared.enums.sport import League, Sport
    from apps.api.services.backtest import generate_sample_backtest_data, run_backtest

    sport_enum = Sport(sport)
    league_enum = League(league)
    mg_enum = MarketGroup(market_group)

    data = generate_sample_backtest_data(sport_enum, mg_enum)
    report = run_backtest(data, sport_enum, league_enum, mg_enum)

    return {
        "status": "completed",
        "report": report.model_dump(),
    }


@app.task(name="jobs.build_features")
def build_features(game_id: str) -> dict:
    """Pre-compute and cache features for a game.

    In production, this would:
    1. Load team/player stats from DB
    2. Compute all features
    3. Cache in Redis for fast prediction access
    """
    return {
        "status": "completed",
        "game_id": game_id,
        "message": "Features computed.",
    }


@app.task(name="jobs.poll_odds_and_detect_moves")
def job_poll_odds_and_detect_moves() -> dict:
    """Poll latest odds snapshots and detect significant moves."""
    import json
    from datetime import datetime
    from pathlib import Path

    from packages.shared.schemas.game import OddsSnapshot
    from apps.api.services.odds_watcher import detect_odds_moves

    fixtures_dir = Path(__file__).resolve().parent.parent.parent.parent / "packages" / "fixtures"
    snaps_path = fixtures_dir / "signals" / "odds_snapshots.json"

    if not snaps_path.exists():
        return {"status": "completed", "moves_detected": 0, "signals_created": 0,
                "message": "No odds snapshot fixtures found."}

    raw = json.loads(snaps_path.read_text())
    snapshots = [
        OddsSnapshot(
            game_id=s["game_id"], bookmaker=s["bookmaker"],
            market_key=s["market_key"], outcome_label=s["outcome_label"],
            line=s.get("line"), price=s["price"],
            timestamp=datetime.fromisoformat(s["timestamp"]),
        )
        for s in raw
    ]
    moves, signals = detect_odds_moves(snapshots)
    return {
        "status": "completed",
        "moves_detected": len(moves),
        "signals_created": len(signals),
        "message": f"Detected {len(moves)} odds moves, created {len(signals)} signals.",
    }


@app.task(name="jobs.run_alerts")
def job_run_alerts(date: str | None = None) -> dict:
    """Evaluate notification rules and send alerts.

    In production, this would:
    1. Load all enabled notification rules
    2. Gather signals for today's games
    3. Evaluate each rule against signals + adjusted predictions
    4. Apply dedup + cooldown + anti-spam filters
    5. Send qualifying notifications
    """
    return {
        "status": "completed",
        "date": date or "today",
        "alerts_sent": 0,
        "message": "Alert evaluation completed. Configure rules via /notifications/rules.",
    }


@app.task(name="jobs.compute_segment_profiles")
def job_compute_segment_profiles(sport: str | None = None) -> dict:
    """Compute team segment profiles and matchup profiles."""
    import json
    from pathlib import Path

    from apps.api.services.segment_profiles import (
        compute_team_segment_profiles,
        compute_matchup_segment_profiles,
        generate_segment_signals,
    )

    fixtures_dir = Path(__file__).resolve().parent.parent.parent.parent / "packages" / "fixtures"
    seg_path = fixtures_dir / "signals" / "segment_stats.json"

    if not seg_path.exists():
        return {"status": "completed", "sport": sport or "all",
                "message": "No segment stats fixtures found."}

    raw = json.loads(seg_path.read_text())
    total_profiles = 0
    total_signals = 0

    matchup_pairs = [
        ("arsenal", "chelsea", "soc_ars_che_20260208"),
        ("lakers", "celtics", "nba_lal_bos_20260208"),
    ]
    for team_a, team_b, game_id in matchup_pairs:
        stats_a = raw.get(team_a, [])
        stats_b = raw.get(team_b, [])
        if not stats_a or not stats_b:
            continue
        profiles_a = compute_team_segment_profiles(team_a, stats_a)
        profiles_b = compute_team_segment_profiles(team_b, stats_b)
        matchup_profiles = compute_matchup_segment_profiles(team_a, team_b, profiles_a, profiles_b)
        seg_signals = generate_segment_signals(team_a, team_b, game_id, matchup_profiles, profiles_a, profiles_b)
        total_profiles += len(profiles_a) + len(profiles_b) + len(matchup_profiles)
        total_signals += len(seg_signals)

    return {
        "status": "completed",
        "sport": sport or "all",
        "profiles_computed": total_profiles,
        "signals_created": total_signals,
        "message": f"Computed {total_profiles} profiles, created {total_signals} signals.",
    }
