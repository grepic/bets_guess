"""Odds Watcher — detects significant odds movements and emits signals."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from packages.shared.enums.market import SignalType
from packages.shared.schemas.signals import IntelligenceSignalOut, OddsMoveOut
from packages.shared.schemas.game import OddsSnapshot


# Threshold: emit signal when implied prob changes by >= 3pp
DELTA_IMPLIED_THRESHOLD = 0.03
# Also emit on any line change
LINE_CHANGE_DETECTION = True


def detect_odds_moves(
    snapshots: list[OddsSnapshot],
    lookback_minutes: int = 120,
) -> tuple[list[OddsMoveOut], list[IntelligenceSignalOut]]:
    """Compare latest odds snapshots against earlier ones to find significant moves.

    Groups snapshots by (game_id, bookmaker, market_key, outcome_label).
    Compares the latest snapshot to the earliest within the lookback window.

    Returns (moves, signals) — moves are the raw moves, signals are the
    IntelligenceSignal objects to persist.
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=lookback_minutes)

    # Group by composite key
    groups: dict[str, list[OddsSnapshot]] = {}
    for snap in snapshots:
        key = f"{snap.game_id}|{snap.bookmaker}|{snap.market_key}|{snap.outcome_label}"
        groups.setdefault(key, []).append(snap)

    moves: list[OddsMoveOut] = []
    signals: list[IntelligenceSignalOut] = []

    for key, snaps in groups.items():
        if len(snaps) < 2:
            continue

        # Sort by timestamp ascending
        snaps.sort(key=lambda s: s.timestamp)

        old = snaps[0]
        new = snaps[-1]

        old_implied = 1.0 / old.price if old.price > 0 else 0.0
        new_implied = 1.0 / new.price if new.price > 0 else 0.0
        delta = new_implied - old_implied

        line_changed = (
            old.line is not None
            and new.line is not None
            and old.line != new.line
        )

        if abs(delta) >= DELTA_IMPLIED_THRESHOLD or (LINE_CHANGE_DETECTION and line_changed):
            move = OddsMoveOut(
                game_id=new.game_id,
                bookmaker=new.bookmaker,
                market_key=new.market_key,
                outcome_label=new.outcome_label,
                old_price=old.price,
                new_price=new.price,
                old_implied_prob=round(old_implied, 4),
                new_implied_prob=round(new_implied, 4),
                delta_implied_prob=round(delta, 4),
                old_line=old.line,
                new_line=new.line,
                detected_at=now,
            )
            moves.append(move)

            # Determine signal strength: larger delta = stronger signal
            strength = min(1.0, abs(delta) / 0.10)  # saturates at 10pp move
            reliability = 0.7 if abs(delta) >= 0.05 else 0.5

            direction = "shortened" if delta > 0 else "drifted"
            headline = (
                f"Odds {direction}: {new.outcome_label} "
                f"({old.price:.2f} → {new.price:.2f}, "
                f"{delta:+.1%}pp implied)"
            )

            signal = IntelligenceSignalOut(
                id=str(uuid.uuid4()),
                sport_id=None,
                game_id=new.game_id,
                signal_type=SignalType.ODDS_MOVE,
                signal_strength=round(strength, 3),
                reliability=round(reliability, 3),
                headline=headline,
                description=(
                    f"Bookmaker {new.bookmaker} moved {new.market_key} "
                    f"{new.outcome_label} from {old.price:.2f} to {new.price:.2f}. "
                    f"Implied probability changed by {delta:+.4f}."
                ),
                affected_market_groups=[new.market_key.split(":")[0]] if ":" in new.market_key else [],
                affected_periods=[],
                metadata={
                    "old_odds": old.price,
                    "new_odds": new.price,
                    "delta_implied_prob": round(delta, 4),
                    "old_line": old.line,
                    "new_line": new.line,
                    "bookmaker": new.bookmaker,
                    "direction": direction,
                },
                created_at=now,
            )
            signals.append(signal)

    # Sort moves by abs delta descending (biggest moves first)
    moves.sort(key=lambda m: abs(m.delta_implied_prob), reverse=True)
    return moves, signals


def detect_line_injuries(
    overrides: list[dict],
    game_id: str,
) -> list[IntelligenceSignalOut]:
    """Generate signals from override data (injuries, lineup confirmations).

    Each override dict: {override_type, player_id, team_id, key, value, note}
    """
    signals: list[IntelligenceSignalOut] = []
    now = datetime.utcnow()

    for ovr in overrides:
        ovr_type = ovr.get("override_type", "")
        player_id = ovr.get("player_id")
        team_id = ovr.get("team_id")
        key = ovr.get("key", "")
        value = ovr.get("value", "")
        note = ovr.get("note", "")

        if ovr_type == "injury" and value.lower() in ("out", "doubtful"):
            sig_type = SignalType.KEY_PLAYER_OUT
            strength = 0.8 if value.lower() == "out" else 0.5
            headline = f"Key player {key}: {value}"
            description = f"Player {player_id or key} is {value}. {note}"
            affected_mgs = [
                "moneyline", "spread", "totals", "team_totals",
            ]
        elif ovr_type == "lineup":
            sig_type = SignalType.LINEUP_CONFIRMED
            strength = 0.6
            headline = f"Lineup confirmed: {key}"
            description = f"Lineup information: {value}. {note}"
            affected_mgs = ["moneyline", "spread", "totals"]
        else:
            continue

        signals.append(IntelligenceSignalOut(
            id=str(uuid.uuid4()),
            game_id=game_id,
            team_id=team_id,
            player_id=player_id,
            signal_type=sig_type,
            signal_strength=strength,
            reliability=0.9,  # official source
            headline=headline,
            description=description,
            affected_market_groups=affected_mgs,
            affected_periods=["ft"],
            metadata={"override_type": ovr_type, "key": key, "value": value},
            created_at=now,
        ))

    return signals
