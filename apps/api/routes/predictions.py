"""Prediction and best-bets endpoints."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query

from packages.shared.enums.market import MarketGroup, Period
from packages.shared.enums.sport import League, Sport
from packages.shared.schemas.game import FilterParams
from apps.api.providers.mock_provider import (
    MockOddsProvider, MockScheduleProvider, MockStatsProvider,
)
from apps.api.services.prediction_service import PredictionService
from apps.api.services.signal_adjuster import adjust_prediction

router = APIRouter(tags=["predictions"])

# Wire up providers
_schedule = MockScheduleProvider()
_stats = MockStatsProvider()
_odds = MockOddsProvider()
_service = PredictionService(_schedule, _stats, _odds)

DISCLAIMER = (
    "DISCLAIMER: SmartBets Pro provides statistical analysis and probability estimates only. "
    "These are NOT guarantees of outcomes. All sports betting involves risk and you may lose money. "
    "Never bet more than you can afford to lose. If you have a gambling problem, call 1-800-522-4700. "
    "Past model performance does not guarantee future results."
)


@router.get("/predictions")
async def get_predictions(
    date: date | None = Query(None),
    sport: str | None = Query(None),
    market_group: str | None = Query(None),
    min_edge: float = Query(0.0),
):
    """Get model predictions for games."""
    sport_enum = Sport(sport) if sport else None
    mg_enum = None
    if market_group:
        try:
            mg_enum = MarketGroup(market_group)
        except ValueError:
            pass

    games = []
    if sport_enum:
        games = await _schedule.get_games(sport_enum, game_date=date)
    else:
        for s in Sport:
            sg = await _schedule.get_games(s, game_date=date)
            games.extend(sg)

    market_groups = [mg_enum] if mg_enum else None

    all_predictions = []
    for game in games:
        preds = await _service.predict_game(game, market_groups)
        for p in preds:
            if min_edge > 0:
                # Check edge against fair odds
                implied = 1.0 / p.fair_odds if p.fair_odds > 0 else 0
                if p.probability - implied < min_edge / 100:
                    continue
            all_predictions.append({
                "game_id": p.game_id,
                "market": p.market_spec.normalized_key,
                "market_group": p.market_spec.market_group.value,
                "outcome": p.outcome.value,
                "outcome_label": p.outcome_label,
                "probability": p.probability,
                "fair_odds": p.fair_odds,
                "interval": [p.interval_low, p.interval_high],
                "factors": [
                    {"name": f.name, "value": f.value, "description": f.description}
                    for f in p.factors
                ],
                "model_version": p.model_version,
            })

    return {
        "count": len(all_predictions),
        "predictions": all_predictions,
        "disclaimer": DISCLAIMER,
    }


@router.get("/best-bets")
async def get_best_bets(
    date: date | None = Query(None),
    sport: str | None = Query(None),
    league: str | None = Query(None),
    market_group: str | None = Query(None),
    min_edge: float = Query(2.0, description="Minimum edge percentage"),
    min_conf: float = Query(0.0, description="Minimum confidence (interval low)"),
    min_prob: float = Query(0.0, description="Minimum probability"),
    hide_no_odds: bool = Query(False, description="Hide bets without bookmaker odds"),
    use_signals: bool = Query(False, description="Apply intelligence signal adjustments"),
    limit: int = Query(50, le=200),
):
    """Get best value bets based on model edge over bookmaker odds."""
    sport_enum = Sport(sport) if sport else None
    league_enum = League(league) if league else None
    mg_enum = None
    if market_group:
        try:
            mg_enum = MarketGroup(market_group)
        except ValueError:
            pass

    filters = FilterParams(
        date=date,
        sport=sport_enum,
        league=league_enum,
        market_group=mg_enum,
        min_edge=min_edge,
        min_probability=min_prob,
        min_confidence=min_conf,
        hide_missing_odds=hide_no_odds,
        limit=limit,
    )

    bets = await _service.generate_best_bets(filters)

    # Apply signal adjustments if requested
    signal_adjusted = []
    if use_signals:
        from apps.api.routes.signals import _signals_store
        for b in bets:
            game_signals = [s for s in _signals_store if s.game_id == b.game_id]
            if game_signals:
                adjusted = adjust_prediction(
                    base_prediction_id=None,
                    game_id=b.game_id,
                    market_key=b.market_spec.normalized_key,
                    outcome_label=b.outcome_label,
                    base_prob=b.model_prob,
                    interval_low=b.interval_low,
                    interval_high=b.interval_high,
                    signals=game_signals,
                    bookmaker_odds=b.bookmaker_odds,
                )
                signal_adjusted.append({
                    "game_id": b.game_id,
                    "market": b.market_spec.normalized_key,
                    "outcome_label": b.outcome_label,
                    "base_prob": adjusted.base_prob,
                    "adjusted_prob": adjusted.adjusted_prob,
                    "adjusted_fair_odds": adjusted.adjusted_fair_odds,
                    "adjusted_edge": adjusted.adjusted_edge,
                    "applied_signals": len(adjusted.applied_signal_ids),
                    "signal_reasons": adjusted.signal_reasons,
                })

    result = {
        "count": len(bets),
        "bets": [b.model_dump() for b in bets],
        "disclaimer": DISCLAIMER,
        "responsible_gambling": (
            "Gambling should be entertaining, not a source of income. "
            "Set limits, take breaks, and never chase losses. "
            "Probabilities shown are model estimates with uncertainty ranges - not certainties."
        ),
    }
    if use_signals and signal_adjusted:
        result["signal_adjustments"] = signal_adjusted
    return result
