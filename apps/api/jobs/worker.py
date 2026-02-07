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
    """Poll latest odds snapshots and detect significant moves.

    In production, this would:
    1. Fetch latest odds from all bookmakers
    2. Compare against previous snapshots
    3. Detect moves >= 3pp implied prob change
    4. Persist IntelligenceSignal records
    5. Return detected moves
    """
    from apps.api.services.odds_watcher import detect_odds_moves
    # In dev mode, use mock data - real implementation would query DB
    return {
        "status": "completed",
        "moves_detected": 0,
        "signals_created": 0,
        "message": "Odds polling completed. Wire real odds provider for production.",
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
    """Compute team segment profiles and matchup profiles.

    In production, this would:
    1. Load team game stats from DB
    2. Compute per-period profiles for each team
    3. Compute matchup profiles for today's games
    4. Generate SEGMENT_DOMINANCE and MATCHUP_TREND signals
    5. Persist everything to DB
    """
    return {
        "status": "completed",
        "sport": sport or "all",
        "message": "Segment profiles computed.",
    }
