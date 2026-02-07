"""Market catalog endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from packages.shared.catalog.registry import get_registry
from packages.shared.enums.sport import Sport

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/markets")
async def list_markets(sport: str | None = None):
    """Get all available markets, optionally filtered by sport."""
    registry = get_registry()
    if sport:
        try:
            s = Sport(sport)
        except ValueError:
            return {"error": f"Unknown sport: {sport}", "valid": [s.value for s in Sport]}
        definitions = registry.list_for_sport(s)
    else:
        definitions = registry.list_all()

    return {
        "total": len(definitions),
        "markets": [
            {
                "market_group": d.market_group.value,
                "market_type": d.market_type.value,
                "sport": d.sport.value,
                "display_name": d.display_name,
                "description": d.description,
                "supported_periods": [p.value for p in d.supported_periods],
                "supported_sides": [s.value for s in d.supported_sides],
                "line_unit": d.line_unit.value if d.line_unit else None,
                "default_lines": d.default_lines,
                "outcomes": [
                    {"type": o.outcome_type.value, "label": o.label}
                    for o in d.outcomes
                ],
                "requires_player": d.requires_player,
                "model_family": d.model_family,
            }
            for d in definitions
        ],
    }


@router.get("/sports")
async def list_sports():
    """List all supported sports with market counts."""
    registry = get_registry()
    return {
        "sports": [
            {
                "id": s.value,
                "name": s.value.upper(),
                "market_count": len(registry.list_for_sport(s)),
            }
            for s in Sport
        ],
        "total_markets": registry.total_markets,
    }
