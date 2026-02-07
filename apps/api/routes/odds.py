"""Odds endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Query

from apps.api.providers.mock_provider import MockOddsProvider

router = APIRouter(tags=["odds"])
odds_provider = MockOddsProvider()


@router.get("/odds")
async def get_odds(
    game_id: str = Query(..., description="Game ID"),
    market_key: str | None = Query(None, description="Filter by market key"),
):
    """Get odds for a specific game."""
    odds = await odds_provider.get_odds(game_id, market_key)
    return {
        "game_id": game_id,
        "count": len(odds),
        "odds": [o.model_dump() for o in odds],
    }
