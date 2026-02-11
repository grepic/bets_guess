"""Signals, notifications, and odds moves endpoints."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query

from packages.shared.enums.market import SignalType
from packages.shared.schemas.signals import (
    AdjustedPredictionOut,
    IntelligenceSignalOut,
    NotificationRuleIn,
    NotificationRuleOut,
    NotificationSentOut,
    OddsMoveOut,
)

router = APIRouter(tags=["signals"])

DISCLAIMER = (
    "DISCLAIMER: Intelligence signals are informational flags based on statistical patterns. "
    "They do NOT guarantee outcomes. All sports betting involves risk. "
    "Never bet more than you can afford to lose."
)

# ────────────────────────────────────────────────────────────
# In-memory stores (dev mode — production uses PostgreSQL)
# ────────────────────────────────────────────────────────────
_rules_store: list[NotificationRuleOut] = []
_sent_store: list[NotificationSentOut] = []
_signals_store: list[IntelligenceSignalOut] = []
_moves_store: list[OddsMoveOut] = []
_adjusted_store: list[AdjustedPredictionOut] = []
_next_rule_id = 1


# ────────────────────────────────────────────────────────────
# Signals
# ────────────────────────────────────────────────────────────

@router.get("/signals")
async def get_signals(
    game_id: str | None = Query(None),
    signal_type: str | None = Query(None),
    limit: int = Query(50, le=200),
):
    """Get intelligence signals, optionally filtered by game and type."""
    results = list(_signals_store)
    if game_id:
        results = [s for s in results if s.game_id == game_id]
    if signal_type:
        try:
            st = SignalType(signal_type)
            results = [s for s in results if s.signal_type == st]
        except ValueError:
            pass
    results.sort(key=lambda s: s.created_at, reverse=True)
    return {
        "count": len(results[:limit]),
        "signals": [s.model_dump() for s in results[:limit]],
        "disclaimer": DISCLAIMER,
    }


# ────────────────────────────────────────────────────────────
# Odds Moves
# ────────────────────────────────────────────────────────────

@router.get("/odds/moves")
async def get_odds_moves(
    game_id: str | None = Query(None),
    min_delta: float = Query(0.0, description="Minimum abs(delta_implied_prob)"),
    limit: int = Query(50, le=200),
):
    """Get significant odds movements."""
    results = list(_moves_store)
    if game_id:
        results = [m for m in results if m.game_id == game_id]
    if min_delta > 0:
        results = [m for m in results if abs(m.delta_implied_prob) >= min_delta]
    results.sort(key=lambda m: abs(m.delta_implied_prob), reverse=True)
    return {
        "count": len(results[:limit]),
        "moves": [m.model_dump() for m in results[:limit]],
        "disclaimer": DISCLAIMER,
    }


# ────────────────────────────────────────────────────────────
# Adjusted Predictions
# ────────────────────────────────────────────────────────────

@router.get("/predictions/adjusted")
async def get_adjusted_predictions(
    game_id: str | None = Query(None),
    market_key: str | None = Query(None),
    min_edge: float = Query(0.0),
    limit: int = Query(50, le=200),
):
    """Get signal-adjusted predictions."""
    results = list(_adjusted_store)
    if game_id:
        results = [p for p in results if p.game_id == game_id]
    if market_key:
        results = [p for p in results if market_key.lower() in p.market_key.lower()]
    if min_edge > 0:
        results = [p for p in results if p.adjusted_edge is not None and p.adjusted_edge >= min_edge]
    results.sort(key=lambda p: p.adjusted_edge or 0, reverse=True)
    return {
        "count": len(results[:limit]),
        "predictions": [p.model_dump() for p in results[:limit]],
        "disclaimer": DISCLAIMER,
    }


# ────────────────────────────────────────────────────────────
# Notification Rules
# ────────────────────────────────────────────────────────────

@router.post("/notifications/rules")
async def create_notification_rule(rule: NotificationRuleIn):
    """Create a new notification rule."""
    global _next_rule_id
    now = datetime.utcnow()
    out = NotificationRuleOut(
        id=_next_rule_id,
        user_key=rule.user_key,
        sports=rule.sports,
        leagues=rule.leagues,
        market_groups=rule.market_groups,
        min_edge=rule.min_edge,
        min_confidence=rule.min_confidence,
        min_prob=rule.min_prob,
        quiet_hours=rule.quiet_hours,
        max_alerts_per_game=rule.max_alerts_per_game,
        max_alerts_per_day=rule.max_alerts_per_day,
        cooldown_minutes=rule.cooldown_minutes,
        enabled=rule.enabled,
        created_at=now,
    )
    _rules_store.append(out)
    _next_rule_id += 1
    return {
        "status": "created",
        "rule": out.model_dump(),
        "disclaimer": DISCLAIMER,
    }


@router.get("/notifications/rules")
async def get_notification_rules(
    user_key: str | None = Query(None),
):
    """Get all notification rules, optionally filtered by user."""
    results = list(_rules_store)
    if user_key:
        results = [r for r in results if r.user_key == user_key]
    return {
        "count": len(results),
        "rules": [r.model_dump() for r in results],
    }


@router.get("/notifications/sent")
async def get_notifications_sent(
    user_key: str | None = Query(None),
    game_id: str | None = Query(None),
    limit: int = Query(50, le=200),
):
    """Get sent notifications."""
    results = list(_sent_store)
    if user_key:
        user_rules = [r.id for r in _rules_store if r.user_key == user_key]
        results = [s for s in results if s.rule_id in user_rules]
    if game_id:
        results = [s for s in results if s.game_id == game_id]
    results.sort(key=lambda s: s.sent_at, reverse=True)
    return {
        "count": len(results[:limit]),
        "notifications": [s.model_dump() for s in results[:limit]],
        "disclaimer": DISCLAIMER,
    }
