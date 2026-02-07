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
