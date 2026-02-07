"""Backtesting engine for model evaluation."""
from __future__ import annotations

import math
from datetime import datetime

from packages.shared.enums.market import MarketGroup
from packages.shared.enums.sport import League, Sport
from packages.shared.schemas.market import BacktestMetrics, BacktestReport


def compute_log_loss(probs: list[float], actuals: list[int]) -> float:
    """Binary log loss."""
    eps = 1e-15
    total = 0.0
    for p, y in zip(probs, actuals):
        p = max(eps, min(1 - eps, p))
        total += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return total / len(probs) if probs else 0.0


def compute_brier_score(probs: list[float], actuals: list[int]) -> float:
    """Brier score."""
    total = sum((p - y) ** 2 for p, y in zip(probs, actuals))
    return total / len(probs) if probs else 0.0


def compute_calibration_error(
    probs: list[float], actuals: list[int], n_bins: int = 10,
) -> float:
    """Expected Calibration Error (ECE)."""
    bins: dict[int, list[tuple[float, int]]] = {i: [] for i in range(n_bins)}
    for p, y in zip(probs, actuals):
        bin_idx = min(int(p * n_bins), n_bins - 1)
        bins[bin_idx].append((p, y))

    ece = 0.0
    n = len(probs)
    for bin_data in bins.values():
        if not bin_data:
            continue
        avg_p = sum(x[0] for x in bin_data) / len(bin_data)
        avg_y = sum(x[1] for x in bin_data) / len(bin_data)
        ece += (len(bin_data) / n) * abs(avg_p - avg_y)
    return ece


def run_backtest(
    predictions: list[dict],
    sport: Sport,
    league: League,
    market_group: MarketGroup,
    model_version: str = "v1.0",
) -> BacktestReport:
    """Run backtest on historical predictions.

    Each prediction dict should have:
    - prob: float (model probability)
    - odds: float (bookmaker decimal odds)
    - won: bool (whether the bet won)
    """
    if not predictions:
        return BacktestReport(
            sport=sport, league=league, market_group=market_group,
            period_start=datetime.utcnow(), period_end=datetime.utcnow(),
            model_version=model_version,
        )

    probs = [p["prob"] for p in predictions]
    actuals = [1 if p["won"] else 0 for p in predictions]
    odds_list = [p["odds"] for p in predictions]

    # Flat stake simulation (1 unit per bet)
    total_bets = len(predictions)
    wins = sum(actuals)
    losses = total_bets - wins
    win_rate = wins / total_bets

    # ROI calculation: profit / total_staked
    profit = sum(
        (odds_list[i] - 1.0) if actuals[i] else -1.0
        for i in range(total_bets)
    )
    roi_pct = (profit / total_bets) * 100

    # Running profit for drawdown
    running = 0.0
    peak = 0.0
    max_dd = 0.0
    for i in range(total_bets):
        running += (odds_list[i] - 1.0) if actuals[i] else -1.0
        peak = max(peak, running)
        dd = peak - running
        max_dd = max(max_dd, dd)

    avg_edge = sum(
        (probs[i] - 1.0 / odds_list[i]) / (1.0 / odds_list[i]) * 100
        if odds_list[i] > 0 else 0.0
        for i in range(total_bets)
    ) / total_bets

    flat_metrics = BacktestMetrics(
        total_bets=total_bets,
        wins=wins,
        losses=losses,
        win_rate=round(win_rate, 4),
        roi_pct=round(roi_pct, 2),
        log_loss=round(compute_log_loss(probs, actuals), 4),
        brier_score=round(compute_brier_score(probs, actuals), 4),
        calibration_error=round(compute_calibration_error(probs, actuals), 4),
        max_drawdown=round(max_dd, 2),
        avg_edge=round(avg_edge, 2),
    )

    # Kelly stake simulation (quarter Kelly, capped at 5%)
    kelly_running = 100.0  # Starting bankroll
    kelly_peak = 100.0
    kelly_max_dd = 0.0
    kelly_wins = 0
    kelly_profit = 0.0

    for i in range(total_bets):
        implied = 1.0 / odds_list[i] if odds_list[i] > 0 else 0.5
        edge = probs[i] - implied
        if edge <= 0:
            continue
        # Quarter Kelly
        kelly_fraction = (edge / (odds_list[i] - 1.0)) * 0.25 if odds_list[i] > 1 else 0
        kelly_fraction = min(kelly_fraction, 0.05)  # Cap at 5%
        stake = kelly_running * kelly_fraction

        if actuals[i]:
            kelly_running += stake * (odds_list[i] - 1.0)
            kelly_wins += 1
            kelly_profit += stake * (odds_list[i] - 1.0)
        else:
            kelly_running -= stake
            kelly_profit -= stake

        kelly_peak = max(kelly_peak, kelly_running)
        kelly_max_dd = max(kelly_max_dd, kelly_peak - kelly_running)

    kelly_roi = (kelly_profit / 100.0) * 100  # % of initial bankroll

    kelly_metrics = BacktestMetrics(
        total_bets=total_bets,
        wins=kelly_wins,
        losses=total_bets - kelly_wins,
        win_rate=round(kelly_wins / total_bets, 4) if total_bets > 0 else 0,
        roi_pct=round(kelly_roi, 2),
        max_drawdown=round(kelly_max_dd, 2),
        avg_edge=round(avg_edge, 2),
    )

    return BacktestReport(
        sport=sport,
        league=league,
        market_group=market_group,
        period_start=datetime(2025, 1, 1),
        period_end=datetime.utcnow(),
        model_version=model_version,
        flat_stake=flat_metrics,
        kelly_stake=kelly_metrics,
        sample_size=total_bets,
        notes="Backtest based on historical fixture data. Past performance does not guarantee future results.",
    )


def generate_sample_backtest_data(
    sport: Sport, market_group: MarketGroup, n: int = 200,
) -> list[dict]:
    """Generate synthetic backtest data for demonstration."""
    import random
    random.seed(42)

    data = []
    for _ in range(n):
        true_prob = random.uniform(0.3, 0.7)
        # Model slightly calibrated with noise
        model_prob = true_prob + random.gauss(0, 0.05)
        model_prob = max(0.05, min(0.95, model_prob))

        # Bookmaker odds with vig
        vig = random.uniform(1.03, 1.08)
        book_odds = vig / true_prob

        won = random.random() < true_prob

        data.append({
            "prob": round(model_prob, 4),
            "odds": round(book_odds, 3),
            "won": won,
        })
    return data
