"""Bet builder endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from packages.shared.enums.market import MarketGroup, MarketType, Period, Side
from packages.shared.enums.sport import Sport
from packages.shared.schemas.market import MarketSpec
from apps.api.providers.mock_provider import (
    MockOddsProvider, MockScheduleProvider, MockStatsProvider,
)
from apps.api.services.prediction_service import PredictionService
from apps.api.services.rules_engine import BetBuilderService

router = APIRouter(prefix="/builder", tags=["builder"])

_schedule = MockScheduleProvider()
_stats = MockStatsProvider()
_odds = MockOddsProvider()
_pred_service = PredictionService(_schedule, _stats, _odds)
_builder_service = BetBuilderService()


class BuilderLegInput(BaseModel):
    market_group: str
    market_type: str = "totals"
    period: str = "ft"
    side: str = "total"
    line_value: float | None = None


class BuilderRequest(BaseModel):
    game_id: str
    legs: list[BuilderLegInput]


@router.post("/validate")
async def validate_builder(request: BuilderRequest):
    """Validate and price a bet builder combination."""
    game = await _schedule.get_game(request.game_id)
    if not game:
        raise HTTPException(404, f"Game {request.game_id} not found")

    # Get all predictions for this game
    predictions = await _pred_service.predict_game(game)

    # Build MarketSpecs from input
    leg_specs = []
    for leg in request.legs:
        try:
            spec = MarketSpec(
                market_group=MarketGroup(leg.market_group),
                market_type=MarketType(leg.market_type),
                period=Period(leg.period),
                side=Side(leg.side),
                line_value=leg.line_value,
            )
            leg_specs.append(spec)
        except ValueError as e:
            raise HTTPException(400, f"Invalid leg specification: {e}")

    proposal = _builder_service.build_proposal(predictions, leg_specs)

    return {
        "proposal": proposal.model_dump(),
        "disclaimer": (
            "Bet builder probabilities are estimates with correlation adjustments. "
            "Combined bets carry higher risk. Never bet more than you can afford to lose."
        ),
    }


@router.get("/suggestions")
async def get_builder_suggestions(
    game_id: str = Query(..., description="Game ID"),
):
    """Get auto-generated bet builder suggestions for a game."""
    game = await _schedule.get_game(game_id)
    if not game:
        raise HTTPException(404, f"Game {game_id} not found")

    predictions = await _pred_service.predict_game(game)
    suggestions = _builder_service.suggest_builders(predictions, game_id)

    return {
        "game_id": game_id,
        "count": len(suggestions),
        "suggestions": [s.model_dump() for s in suggestions],
        "disclaimer": (
            "These are algorithmically generated suggestions, NOT recommendations. "
            "All combinations carry risk. Past model performance does not guarantee future results."
        ),
    }
