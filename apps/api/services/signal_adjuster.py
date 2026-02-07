"""Signal Adjuster — apply intelligence signals to base predictions."""
from __future__ import annotations

import math
from datetime import datetime

from packages.shared.enums.market import SignalType
from packages.shared.schemas.signals import AdjustedPredictionOut, IntelligenceSignalOut


# Adjustment caps per signal type (in probability points)
SIGNAL_CAPS: dict[SignalType, float] = {
    SignalType.ODDS_MOVE: 0.00,           # flag only — no prob adjustment
    SignalType.LINEUP_CONFIRMED: 0.02,    # ±2pp
    SignalType.KEY_PLAYER_OUT: 0.06,      # ±6pp
    SignalType.MATCHUP_TREND: 0.03,       # ±3pp
    SignalType.SEGMENT_DOMINANCE: 0.04,   # ±4pp
    SignalType.FATIGUE_EDGE: 0.03,        # ±3pp
    SignalType.REST_ADVANTAGE: 0.03,      # ±3pp
    SignalType.SCHEDULE_PRESSURE: 0.03,   # ±3pp
    SignalType.PLAYOFF_CONTEXT: 0.03,     # ±3pp
    SignalType.SEASON_TREND: 0.02,        # ±2pp
}

# Maximum total adjustment across all signals
MAX_TOTAL_ADJUSTMENT = 0.12  # ±12pp


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def compute_signal_adjustment(
    signal: IntelligenceSignalOut,
    market_key: str,
    outcome_label: str,
) -> tuple[float, str]:
    """Compute the probability adjustment for a single signal.

    Returns (delta_prob, reason_text).
    delta_prob > 0 means the outcome is MORE likely.
    """
    cap = SIGNAL_CAPS.get(signal.signal_type, 0.02)
    if cap == 0.0:
        # Flag-only signal (e.g., ODDS_MOVE)
        return 0.0, f"{signal.signal_type.value}: flagged (no prob adj)"

    # Base adjustment = strength * reliability * cap
    raw = signal.signal_strength * signal.reliability * cap

    # Direction heuristic: check if the signal's team/context favors the outcome
    # For KEY_PLAYER_OUT: negative for the affected team, positive for opponent
    direction = _infer_direction(signal, outcome_label)
    delta = raw * direction

    # Clamp to cap
    delta = _clamp(delta, -cap, cap)

    reason = (
        f"{signal.signal_type.value}: {signal.headline} "
        f"(strength={signal.signal_strength:.2f}, "
        f"reliability={signal.reliability:.2f}, "
        f"adj={delta:+.4f})"
    )
    return delta, reason


def _infer_direction(signal: IntelligenceSignalOut, outcome_label: str) -> float:
    """Infer whether the signal makes the outcome more or less likely.

    +1.0 = more likely, -1.0 = less likely, 0.0 = neutral.
    """
    sig_type = signal.signal_type
    meta = signal.metadata or {}

    if sig_type == SignalType.KEY_PLAYER_OUT:
        # If the player's team is in the outcome label, reduce prob
        team = meta.get("key", signal.team_id or "")
        out_lower = outcome_label.lower()
        if team and team.lower() in out_lower:
            return -1.0
        return 0.5  # mild positive for opponent

    if sig_type == SignalType.SEGMENT_DOMINANCE:
        dominant = meta.get("dominant_team", "")
        out_lower = outcome_label.lower()
        if dominant and dominant.lower() in out_lower:
            return 1.0
        return -0.5

    if sig_type == SignalType.MATCHUP_TREND:
        favored = meta.get("favored_team", "")
        out_lower = outcome_label.lower()
        if favored and favored.lower() in out_lower:
            return 1.0
        return -0.3

    if sig_type in (SignalType.FATIGUE_EDGE, SignalType.REST_ADVANTAGE):
        # Positive for the advantaged team
        return 0.5

    if sig_type == SignalType.SCHEDULE_PRESSURE:
        return -0.3  # generally negative (team under pressure)

    if sig_type == SignalType.PLAYOFF_CONTEXT:
        return 0.3  # generally positive (teams try harder)

    if sig_type == SignalType.SEASON_TREND:
        direction_val = meta.get("direction", "")
        if direction_val == "up":
            return 0.5
        elif direction_val == "down":
            return -0.5
        return 0.0

    if sig_type == SignalType.LINEUP_CONFIRMED:
        return 0.2  # mild positive for certainty

    return 0.0


def adjust_prediction(
    base_prediction_id: int | None,
    game_id: str,
    market_key: str,
    outcome_label: str,
    base_prob: float,
    interval_low: float,
    interval_high: float,
    signals: list[IntelligenceSignalOut],
    bookmaker_odds: float | None = None,
) -> AdjustedPredictionOut:
    """Apply all relevant signals to a base prediction.

    Caps:
    - Each signal type is capped individually (SIGNAL_CAPS)
    - Total cumulative adjustment is capped at ±12pp (MAX_TOTAL_ADJUSTMENT)
    - CI widens by 1pp per applied signal

    Returns AdjustedPredictionOut with all adjustments applied.
    """
    total_delta = 0.0
    applied_ids: list[str] = []
    reasons: list[dict] = []

    for signal in signals:
        # Check market relevance
        if signal.affected_market_groups:
            mk_base = market_key.split(":")[0] if ":" in market_key else market_key
            relevant = any(
                mg.lower() in mk_base.lower()
                for mg in signal.affected_market_groups
            )
            if not relevant:
                continue

        delta, reason = compute_signal_adjustment(signal, market_key, outcome_label)

        if delta == 0.0 and signal.signal_type != SignalType.ODDS_MOVE:
            continue

        # Accumulate, respecting total cap
        new_total = total_delta + delta
        new_total = _clamp(new_total, -MAX_TOTAL_ADJUSTMENT, MAX_TOTAL_ADJUSTMENT)
        delta = new_total - total_delta  # actual applied delta
        total_delta = new_total

        applied_ids.append(signal.id)
        reasons.append({
            "signal_id": signal.id,
            "signal_type": signal.signal_type.value,
            "headline": signal.headline,
            "delta": round(delta, 4),
            "reason": reason,
        })

    # Apply adjustment
    adjusted_prob = _clamp(base_prob + total_delta, 0.001, 0.999)
    adjusted_fair_odds = round(1.0 / adjusted_prob, 3)

    # Widen confidence interval by 1pp per signal applied
    n_signals = len(applied_ids)
    ci_widening = n_signals * 0.01
    adj_low = _clamp(interval_low - ci_widening, 0.001, 0.999)
    adj_high = _clamp(interval_high + ci_widening, 0.001, 0.999)

    # Compute edge if bookmaker odds available
    adjusted_edge = None
    if bookmaker_odds and bookmaker_odds > 1.0:
        implied = 1.0 / bookmaker_odds
        adjusted_edge = round((adjusted_prob - implied) / implied * 100, 2)

    return AdjustedPredictionOut(
        id=0,
        base_prediction_id=base_prediction_id or 0,
        game_id=game_id,
        market_key=market_key,
        outcome_label=outcome_label,
        base_prob=round(base_prob, 4),
        adjusted_prob=round(adjusted_prob, 4),
        adjusted_fair_odds=adjusted_fair_odds,
        adjusted_edge=adjusted_edge,
        interval_low=round(adj_low, 4),
        interval_high=round(adj_high, 4),
        applied_signal_ids=applied_ids,
        signal_reasons=reasons,
        created_at=datetime.utcnow(),
    )


def adjust_predictions_batch(
    predictions: list[dict],
    signals: list[IntelligenceSignalOut],
    bookmaker_odds_map: dict[str, float] | None = None,
) -> list[AdjustedPredictionOut]:
    """Adjust a batch of predictions with the given signals.

    predictions: list of dicts with keys:
        id, game_id, market_key, outcome_label, probability,
        interval_low, interval_high

    Returns list of AdjustedPredictionOut.
    """
    results = []
    odds_map = bookmaker_odds_map or {}

    for pred in predictions:
        game_id = pred["game_id"]
        market_key = pred["market_key"]

        # Filter signals relevant to this game
        game_signals = [s for s in signals if s.game_id == game_id or s.game_id is None]

        odds_key = f"{market_key}:{pred['outcome_label']}"
        book_odds = odds_map.get(odds_key)

        adjusted = adjust_prediction(
            base_prediction_id=pred.get("id"),
            game_id=game_id,
            market_key=market_key,
            outcome_label=pred["outcome_label"],
            base_prob=pred["probability"],
            interval_low=pred.get("interval_low", pred["probability"] - 0.05),
            interval_high=pred.get("interval_high", pred["probability"] + 0.05),
            signals=game_signals,
            bookmaker_odds=book_odds,
        )
        results.append(adjusted)

    return results
