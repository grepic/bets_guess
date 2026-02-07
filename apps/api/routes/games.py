"""Game and schedule endpoints."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from packages.shared.enums.sport import League, Sport
from apps.api.providers.mock_provider import MockScheduleProvider

router = APIRouter(tags=["games"])
schedule_provider = MockScheduleProvider()


@router.get("/games")
async def list_games(
    date: date | None = Query(None, description="Filter by date (YYYY-MM-DD)"),
    sport: str | None = Query(None, description="Filter by sport"),
    league: str | None = Query(None, description="Filter by league"),
):
    """List games with optional filters."""
    sport_enum = None
    league_enum = None

    if sport:
        try:
            sport_enum = Sport(sport)
        except ValueError:
            raise HTTPException(400, f"Unknown sport: {sport}")

    if league:
        try:
            league_enum = League(league)
        except ValueError:
            raise HTTPException(400, f"Unknown league: {league}")

    if sport_enum:
        games = await schedule_provider.get_games(sport_enum, league_enum, date)
    else:
        games = []
        for s in Sport:
            sg = await schedule_provider.get_games(s, league_enum, date)
            games.extend(sg)

    return {
        "count": len(games),
        "games": [g.model_dump() for g in games],
    }


@router.get("/games/{game_id}")
async def get_game(game_id: str):
    """Get details for a specific game."""
    game = await schedule_provider.get_game(game_id)
    if not game:
        raise HTTPException(404, f"Game {game_id} not found")
    return game.model_dump()
