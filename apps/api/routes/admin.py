"""Admin and job endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException

from packages.shared.enums.market import MarketGroup
from packages.shared.enums.sport import League, Sport
from packages.shared.schemas.game import OverrideRequest
from apps.api.core.config import get_settings
from apps.api.services.backtest import generate_sample_backtest_data, run_backtest

router = APIRouter(tags=["admin"])


def verify_admin_token(authorization: str = Header(...)):
    settings = get_settings()
    if authorization != f"Bearer {settings.admin_token}":
        raise HTTPException(403, "Invalid admin token")


@router.post("/admin/overrides")
async def create_override(
    override: OverrideRequest,
    _: None = Depends(verify_admin_token),
):
    """Create a manual override (injury, minutes, lineup)."""
    # In production, this would persist to DB
    return {
        "status": "created",
        "override": override.model_dump(),
        "note": "Override registered. Will be applied to next prediction run.",
    }


@router.post("/jobs/ingest")
async def trigger_ingest(
    _: None = Depends(verify_admin_token),
):
    """Trigger data ingestion job."""
    # In production, this would enqueue a Celery task
    return {
        "status": "queued",
        "job_type": "ingest",
        "message": "Data ingestion job queued. Using mock fixtures in dev mode.",
    }


@router.post("/jobs/predict")
async def trigger_predict(
    _: None = Depends(verify_admin_token),
):
    """Trigger prediction generation job."""
    return {
        "status": "queued",
        "job_type": "predict",
        "message": "Prediction job queued.",
    }


@router.get("/reports/backtest")
async def get_backtest_report(
    league: str | None = None,
    market_group: str | None = None,
    sport: str | None = None,
):
    """Get backtest report for a sport/league/market combination."""
    sport_enum = Sport(sport) if sport else Sport.SOCCER
    league_enum = League(league) if league else League.EPL

    mg_enum = MarketGroup.TOTALS
    if market_group:
        try:
            mg_enum = MarketGroup(market_group)
        except ValueError:
            pass

    # Generate sample data for demo
    data = generate_sample_backtest_data(sport_enum, mg_enum)
    report = run_backtest(data, sport_enum, league_enum, mg_enum)

    return {
        "report": report.model_dump(),
        "disclaimer": (
            "This backtest uses simulated historical data for demonstration. "
            "Real backtests require actual historical odds and results data. "
            "Past performance does not guarantee future results."
        ),
    }
