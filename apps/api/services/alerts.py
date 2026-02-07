"""Alerts Engine — evaluate notification rules, enforce dedup + cooldown + anti-spam."""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta

from packages.shared.schemas.signals import (
    AdjustedPredictionOut,
    IntelligenceSignalOut,
    NotificationRuleOut,
    NotificationSentOut,
)


def _compute_dedup_hash(
    game_id: str,
    market_key: str,
    line: float | None,
    selection: str,
    rule_id: int,
) -> str:
    """Dedup hash = sha256(game_id + market_key + line + selection + rule_id)."""
    raw = f"{game_id}|{market_key}|{line}|{selection}|{rule_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _check_cooldown(
    rule: NotificationRuleOut,
    sent_history: list[NotificationSentOut],
    now: datetime,
) -> bool:
    """Return True if cooldown has elapsed since last sent notification for this rule."""
    if not sent_history:
        return True
    latest = max(sent_history, key=lambda s: s.sent_at)
    elapsed = (now - latest.sent_at).total_seconds() / 60.0
    return elapsed >= rule.cooldown_minutes


def _check_daily_cap(
    rule: NotificationRuleOut,
    sent_history: list[NotificationSentOut],
    now: datetime,
) -> bool:
    """Return True if daily alert cap not exceeded."""
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = sum(1 for s in sent_history if s.sent_at >= today_start)
    return today_count < rule.max_alerts_per_day


def _check_game_cap(
    rule: NotificationRuleOut,
    game_id: str,
    sent_history: list[NotificationSentOut],
) -> bool:
    """Return True if per-game alert cap not exceeded."""
    game_count = sum(1 for s in sent_history if s.game_id == game_id)
    return game_count < rule.max_alerts_per_game


def _check_quiet_hours(
    rule: NotificationRuleOut,
    now: datetime,
) -> bool:
    """Return True if NOT in quiet hours (ok to send)."""
    qh = rule.quiet_hours
    if not qh or "start" not in qh or "end" not in qh:
        return True
    try:
        start_h, start_m = map(int, qh["start"].split(":"))
        end_h, end_m = map(int, qh["end"].split(":"))
        now_minutes = now.hour * 60 + now.minute
        start_minutes = start_h * 60 + start_m
        end_minutes = end_h * 60 + end_m

        if start_minutes <= end_minutes:
            # Same day range, e.g., 23:00 - 07:00 wraps
            return not (start_minutes <= now_minutes < end_minutes)
        else:
            # Wraps midnight
            return not (now_minutes >= start_minutes or now_minutes < end_minutes)
    except (ValueError, AttributeError):
        return True


def evaluate_rule(
    rule: NotificationRuleOut,
    adjusted_predictions: list[AdjustedPredictionOut],
    signals: list[IntelligenceSignalOut],
    sent_history: list[NotificationSentOut],
) -> list[NotificationSentOut]:
    """Evaluate a single notification rule against predictions and signals.

    Requirements:
    - At least 2 distinct signal types must be present for the game
    - Edge must meet rule.min_edge
    - Probability must meet rule.min_prob
    - Dedup: same hash not sent before
    - Cooldown: enough time since last alert
    - Daily cap: not exceeded
    - Per-game cap: not exceeded
    - Quiet hours: not in quiet period
    """
    now = datetime.utcnow()

    if not rule.enabled:
        return []

    # Check quiet hours
    if not _check_quiet_hours(rule, now):
        return []

    # Check cooldown
    if not _check_cooldown(rule, sent_history, now):
        return []

    # Check daily cap
    if not _check_daily_cap(rule, sent_history, now):
        return []

    new_notifications: list[NotificationSentOut] = []

    # Group signals by game_id
    signals_by_game: dict[str, list[IntelligenceSignalOut]] = {}
    for sig in signals:
        if sig.game_id:
            signals_by_game.setdefault(sig.game_id, []).append(sig)

    for pred in adjusted_predictions:
        game_id = pred.game_id

        # Sport/league filter (if rule specifies any)
        # (In production, predictions would carry sport/league info)

        # Check per-game cap
        if not _check_game_cap(rule, game_id, sent_history + new_notifications):
            continue

        # Check min edge
        if pred.adjusted_edge is not None and pred.adjusted_edge < rule.min_edge:
            continue

        # Check min prob
        if pred.adjusted_prob < rule.min_prob:
            continue

        # Check min confidence (interval_low)
        if rule.min_confidence > 0 and pred.interval_low < rule.min_confidence:
            continue

        # CRITICAL: Require at least 2 distinct signal types for this game
        game_signals = signals_by_game.get(game_id, [])
        distinct_types = set(s.signal_type for s in game_signals)
        if len(distinct_types) < 2:
            continue

        # Market group filter
        if rule.market_groups:
            mk_base = pred.market_key.split(":")[0] if ":" in pred.market_key else pred.market_key
            if not any(mg.lower() in mk_base.lower() for mg in rule.market_groups):
                continue

        # Dedup check
        dedup = _compute_dedup_hash(
            game_id, pred.market_key, None, pred.outcome_label, rule.id,
        )
        if any(s.dedup_hash == dedup for s in sent_history):
            continue
        if any(s.dedup_hash == dedup for s in new_notifications):
            continue

        # Build signals summary
        relevant_signals = [
            s for s in game_signals
            if not s.affected_market_groups
            or any(mg.lower() in pred.market_key.lower() for mg in s.affected_market_groups)
        ]
        signals_summary = [
            {
                "signal_id": s.id,
                "type": s.signal_type.value,
                "headline": s.headline,
                "strength": s.signal_strength,
            }
            for s in relevant_signals[:5]  # Limit to 5 most relevant
        ]

        notification = NotificationSentOut(
            id=0,
            rule_id=rule.id,
            game_id=game_id,
            market_key=pred.market_key,
            line=None,
            selection=pred.outcome_label,
            edge_pct=pred.adjusted_edge or 0.0,
            model_prob=pred.adjusted_prob,
            fair_odds=pred.adjusted_fair_odds,
            signals_summary=signals_summary,
            payload={
                "base_prob": pred.base_prob,
                "adjusted_prob": pred.adjusted_prob,
                "n_signals": len(relevant_signals),
                "distinct_signal_types": list(distinct_types),
                "interval": [pred.interval_low, pred.interval_high],
            },
            sent_at=now,
            dedup_hash=dedup,
        )
        new_notifications.append(notification)

        # Re-check daily cap after adding
        if not _check_daily_cap(rule, sent_history + new_notifications, now):
            break

    return new_notifications


def evaluate_rules_for_date(
    rules: list[NotificationRuleOut],
    adjusted_predictions: list[AdjustedPredictionOut],
    signals: list[IntelligenceSignalOut],
    sent_history_by_rule: dict[int, list[NotificationSentOut]],
) -> list[NotificationSentOut]:
    """Evaluate all rules for a date and return new notifications to send.

    sent_history_by_rule: {rule_id: [previously sent notifications]}
    """
    all_new: list[NotificationSentOut] = []

    for rule in rules:
        if not rule.enabled:
            continue
        history = sent_history_by_rule.get(rule.id, [])
        new_notifs = evaluate_rule(rule, adjusted_predictions, signals, history)
        all_new.extend(new_notifs)

    return all_new
