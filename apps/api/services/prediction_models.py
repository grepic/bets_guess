"""Prediction models for all market types across sports."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from packages.shared.enums.market import MarketGroup, OutcomeType, Period
from packages.shared.schemas.market import ExplanationFactor, PredictionResult, MarketSpec
from apps.api.services.features import PlayerFeatures, TeamFeatures


# ────────────────────────────────────────────────────────────
# Poisson helpers
# ────────────────────────────────────────────────────────────

def poisson_pmf(k: int, lam: float) -> float:
    """P(X = k) for Poisson with rate lam."""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def poisson_cdf(k: int, lam: float) -> float:
    """P(X <= k)."""
    return sum(poisson_pmf(i, lam) for i in range(k + 1))


def poisson_over(line: float, lam: float) -> float:
    """P(X > line). For .5 lines, this is P(X >= ceil(line))."""
    threshold = int(math.ceil(line))
    return 1.0 - poisson_cdf(threshold - 1, lam)


def poisson_under(line: float, lam: float) -> float:
    """P(X < line). For .5 lines, P(X <= floor(line))."""
    threshold = int(math.floor(line))
    return poisson_cdf(threshold, lam)


def build_score_matrix(home_lam: float, away_lam: float, max_goals: int = 8) -> list[list[float]]:
    """Build joint probability matrix P(home=i, away=j)."""
    matrix = []
    for i in range(max_goals + 1):
        row = []
        for j in range(max_goals + 1):
            row.append(poisson_pmf(i, home_lam) * poisson_pmf(j, away_lam))
        matrix.append(row)
    return matrix


# ────────────────────────────────────────────────────────────
# Normal distribution helpers (for NBA totals)
# ────────────────────────────────────────────────────────────

def norm_cdf(x: float, mu: float, sigma: float) -> float:
    """Approximate normal CDF."""
    if sigma <= 0:
        return 1.0 if x >= mu else 0.0
    return 0.5 * (1.0 + math.erf((x - mu) / (sigma * math.sqrt(2))))


def norm_over(line: float, mu: float, sigma: float) -> float:
    return 1.0 - norm_cdf(line, mu, sigma)


def norm_under(line: float, mu: float, sigma: float) -> float:
    return norm_cdf(line, mu, sigma)


# ────────────────────────────────────────────────────────────
# ELO helpers (for Tennis)
# ────────────────────────────────────────────────────────────

def elo_win_prob(elo_a: float, elo_b: float) -> float:
    """Expected score for player A vs B from ELO ratings."""
    return 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / 400.0))


# ────────────────────────────────────────────────────────────
# Confidence interval (bootstrap-lite heuristic)
# ────────────────────────────────────────────────────────────

def confidence_interval(prob: float, sample_size: int = 50) -> tuple[float, float]:
    """Heuristic confidence interval based on sample size.
    Uses Wilson score-like approach simplified.
    """
    z = 1.96  # 95% CI
    n = max(sample_size, 10)
    denominator = 1 + z * z / n
    center = (prob + z * z / (2 * n)) / denominator
    margin = z * math.sqrt((prob * (1 - prob) + z * z / (4 * n)) / n) / denominator
    low = max(0.0, center - margin)
    high = min(1.0, center + margin)
    return (round(low, 4), round(high, 4))


# ────────────────────────────────────────────────────────────
# Soccer Poisson model
# ────────────────────────────────────────────────────────────

HOME_ADVANTAGE_SOCCER = 0.25  # ~0.25 goal home advantage


class SoccerPoissonModel:
    """Poisson-based model for soccer markets."""

    def predict_lambdas(
        self, home: TeamFeatures, away: TeamFeatures,
    ) -> tuple[float, float]:
        """Predict expected goals for home and away."""
        # Dixon-Coles style: lambda = attack * defense * league_avg * home_adv
        home_attack = home.attack_rating if home.attack_rating > 0 else 1.0
        away_defense = away.defense_rating if away.defense_rating > 0 else 1.0
        away_attack = away.attack_rating if away.attack_rating > 0 else 1.0
        home_defense = home.defense_rating if home.defense_rating > 0 else 1.0

        league_avg = 1.35
        home_lam = home_attack * away_defense * league_avg + HOME_ADVANTAGE_SOCCER * 0.5
        away_lam = away_attack * home_defense * league_avg - HOME_ADVANTAGE_SOCCER * 0.3

        # Blend with xG if available
        if home.xg_for_avg > 0 and away.xg_for_avg > 0:
            home_lam = 0.6 * home_lam + 0.4 * home.xg_for_avg
            away_lam = 0.6 * away_lam + 0.4 * away.xg_for_avg

        # Form adjustment
        form_adj_h = (home.form_last5_win_pct - 0.5) * 0.2
        form_adj_a = (away.form_last5_win_pct - 0.5) * 0.2
        home_lam = max(0.3, home_lam + form_adj_h)
        away_lam = max(0.3, away_lam + form_adj_a)

        return (home_lam, away_lam)

    def predict_1x2(
        self, home: TeamFeatures, away: TeamFeatures,
    ) -> dict[str, float]:
        h_lam, a_lam = self.predict_lambdas(home, away)
        matrix = build_score_matrix(h_lam, a_lam)
        home_win = sum(matrix[i][j] for i in range(9) for j in range(i))
        draw = sum(matrix[i][i] for i in range(9))
        away_win = sum(matrix[i][j] for i in range(9) for j in range(i + 1, 9))
        total = home_win + draw + away_win
        return {
            "home": home_win / total,
            "draw": draw / total,
            "away": away_win / total,
        }

    def predict_totals(
        self, home: TeamFeatures, away: TeamFeatures, line: float,
    ) -> dict[str, float]:
        h_lam, a_lam = self.predict_lambdas(home, away)
        total_lam = h_lam + a_lam
        over = poisson_over(line, total_lam)
        under = poisson_under(line, total_lam)
        return {"over": over, "under": under}

    def predict_team_totals(
        self, home: TeamFeatures, away: TeamFeatures, side: str, line: float,
    ) -> dict[str, float]:
        h_lam, a_lam = self.predict_lambdas(home, away)
        lam = h_lam if side == "home" else a_lam
        return {"over": poisson_over(line, lam), "under": poisson_under(line, lam)}

    def predict_btts(
        self, home: TeamFeatures, away: TeamFeatures,
    ) -> dict[str, float]:
        h_lam, a_lam = self.predict_lambdas(home, away)
        p_home_scores = 1.0 - poisson_pmf(0, h_lam)
        p_away_scores = 1.0 - poisson_pmf(0, a_lam)
        btts = p_home_scores * p_away_scores
        return {"yes": btts, "no": 1.0 - btts}

    def predict_clean_sheet(
        self, home: TeamFeatures, away: TeamFeatures, side: str,
    ) -> dict[str, float]:
        h_lam, a_lam = self.predict_lambdas(home, away)
        opp_lam = a_lam if side == "home" else h_lam
        cs = poisson_pmf(0, opp_lam)
        return {"yes": cs, "no": 1.0 - cs}

    def predict_correct_score(
        self, home: TeamFeatures, away: TeamFeatures, top_n: int = 10,
    ) -> list[dict]:
        h_lam, a_lam = self.predict_lambdas(home, away)
        matrix = build_score_matrix(h_lam, a_lam)
        scores = []
        for i in range(7):
            for j in range(7):
                scores.append({
                    "home": i, "away": j,
                    "prob": matrix[i][j],
                    "label": f"{i}-{j}",
                })
        scores.sort(key=lambda x: x["prob"], reverse=True)
        return scores[:top_n]

    def predict_win_to_nil(
        self, home: TeamFeatures, away: TeamFeatures, side: str,
    ) -> dict[str, float]:
        h_lam, a_lam = self.predict_lambdas(home, away)
        matrix = build_score_matrix(h_lam, a_lam)
        if side == "home":
            p = sum(matrix[i][0] for i in range(1, 9))
        else:
            p = sum(matrix[0][j] for j in range(1, 9))
        return {"yes": p, "no": 1.0 - p}

    def predict_winning_margin(
        self, home: TeamFeatures, away: TeamFeatures,
    ) -> list[dict]:
        h_lam, a_lam = self.predict_lambdas(home, away)
        matrix = build_score_matrix(h_lam, a_lam)
        buckets = {
            "Home by 1": 0.0, "Home by 2": 0.0, "Home by 3+": 0.0,
            "Draw": 0.0,
            "Away by 1": 0.0, "Away by 2": 0.0, "Away by 3+": 0.0,
        }
        for i in range(9):
            for j in range(9):
                diff = i - j
                p = matrix[i][j]
                if diff == 0:
                    buckets["Draw"] += p
                elif diff == 1:
                    buckets["Home by 1"] += p
                elif diff == 2:
                    buckets["Home by 2"] += p
                elif diff >= 3:
                    buckets["Home by 3+"] += p
                elif diff == -1:
                    buckets["Away by 1"] += p
                elif diff == -2:
                    buckets["Away by 2"] += p
                elif diff <= -3:
                    buckets["Away by 3+"] += p
        return [{"label": k, "prob": v} for k, v in buckets.items()]

    def predict_corners_total(
        self, home: TeamFeatures, away: TeamFeatures, line: float,
    ) -> dict[str, float]:
        total_lam = home.corners_for_avg + away.corners_for_avg
        if total_lam <= 0:
            total_lam = 10.0  # league average fallback
        return {"over": poisson_over(line, total_lam), "under": poisson_under(line, total_lam)}

    def predict_corners_team(
        self, home: TeamFeatures, away: TeamFeatures, side: str, line: float,
    ) -> dict[str, float]:
        lam = home.corners_for_avg if side == "home" else away.corners_for_avg
        if lam <= 0:
            lam = 5.0
        return {"over": poisson_over(line, lam), "under": poisson_under(line, lam)}

    def predict_cards_total(
        self, home: TeamFeatures, away: TeamFeatures, line: float,
    ) -> dict[str, float]:
        total_lam = home.cards_for_avg + away.cards_for_avg
        if total_lam <= 0:
            total_lam = 4.0
        return {"over": poisson_over(line, total_lam), "under": poisson_under(line, total_lam)}

    def predict_cards_team(
        self, home: TeamFeatures, away: TeamFeatures, side: str, line: float,
    ) -> dict[str, float]:
        lam = home.cards_for_avg if side == "home" else away.cards_for_avg
        if lam <= 0:
            lam = 2.0
        return {"over": poisson_over(line, lam), "under": poisson_under(line, lam)}

    def predict_shots_total(
        self, home: TeamFeatures, away: TeamFeatures, line: float,
    ) -> dict[str, float]:
        total_lam = home.shots_avg + away.shots_avg
        if total_lam <= 0:
            total_lam = 22.0
        return {"over": poisson_over(line, total_lam), "under": poisson_under(line, total_lam)}

    def predict_sot_total(
        self, home: TeamFeatures, away: TeamFeatures, line: float,
    ) -> dict[str, float]:
        total_lam = home.sot_avg + away.sot_avg
        if total_lam <= 0:
            total_lam = 9.0
        return {"over": poisson_over(line, total_lam), "under": poisson_under(line, total_lam)}

    def predict_shots_team(
        self, home: TeamFeatures, away: TeamFeatures, side: str, line: float,
    ) -> dict[str, float]:
        lam = home.shots_avg if side == "home" else away.shots_avg
        if lam <= 0:
            lam = 11.0
        return {"over": poisson_over(line, lam), "under": poisson_under(line, lam)}

    def predict_sot_team(
        self, home: TeamFeatures, away: TeamFeatures, side: str, line: float,
    ) -> dict[str, float]:
        lam = home.sot_avg if side == "home" else away.sot_avg
        if lam <= 0:
            lam = 4.5
        return {"over": poisson_over(line, lam), "under": poisson_under(line, lam)}

    def predict_player_sot(
        self, player: PlayerFeatures, line: float,
    ) -> dict[str, float]:
        lam = player.soccer_sot_avg if player.soccer_sot_avg > 0 else 0.8
        return {"over": poisson_over(line, lam), "under": poisson_under(line, lam)}

    def predict_anytime_scorer(
        self, player: PlayerFeatures, team_lam: float,
    ) -> dict[str, float]:
        """Anytime goalscorer using player share of team goals."""
        player_goal_rate = player.soccer_goals_avg if player.soccer_goals_avg > 0 else 0.1
        p_score = 1.0 - poisson_pmf(0, player_goal_rate)
        return {"yes": p_score, "no": 1.0 - p_score}

    def predict_player_card(
        self, player: PlayerFeatures,
    ) -> dict[str, float]:
        rate = player.soccer_cards_avg if player.soccer_cards_avg > 0 else 0.15
        p = 1.0 - poisson_pmf(0, rate)
        return {"yes": p, "no": 1.0 - p}

    def predict_red_card(
        self, home: TeamFeatures, away: TeamFeatures,
    ) -> dict[str, float]:
        red_rate = 0.08  # ~8% of matches have a red card on average
        # Adjust by cards history
        total_cards = home.cards_for_avg + away.cards_for_avg
        if total_cards > 5:
            red_rate *= 1.3
        elif total_cards < 3:
            red_rate *= 0.7
        return {"yes": red_rate, "no": 1.0 - red_rate}

    def get_factors(
        self, home: TeamFeatures, away: TeamFeatures, market_group: str,
    ) -> list[ExplanationFactor]:
        h_lam, a_lam = self.predict_lambdas(home, away)
        factors = [
            ExplanationFactor(
                name="Home Attack Rating", value=round(home.attack_rating, 3),
                description=f"{home.team_id} attack strength relative to league average",
                importance=0.25,
            ),
            ExplanationFactor(
                name="Away Attack Rating", value=round(away.attack_rating, 3),
                description=f"{away.team_id} attack strength relative to league average",
                importance=0.25,
            ),
            ExplanationFactor(
                name="Home Form (L5)", value=round(home.form_last5_win_pct, 3),
                description=f"Win rate in last 5 matches",
                importance=0.15,
            ),
            ExplanationFactor(
                name="Expected Goals Home", value=round(h_lam, 3),
                description=f"Model expected goals for home team",
                importance=0.2,
            ),
            ExplanationFactor(
                name="Expected Goals Away", value=round(a_lam, 3),
                description=f"Model expected goals for away team",
                importance=0.15,
            ),
        ]
        if "corner" in market_group:
            factors.extend([
                ExplanationFactor(
                    name="Home Corners Avg", value=round(home.corners_for_avg, 2),
                    description="Average corners per game (home team)",
                    importance=0.3,
                ),
                ExplanationFactor(
                    name="Away Corners Avg", value=round(away.corners_for_avg, 2),
                    description="Average corners per game (away team)",
                    importance=0.3,
                ),
            ])
        if "card" in market_group:
            factors.extend([
                ExplanationFactor(
                    name="Home Cards Avg", value=round(home.cards_for_avg, 2),
                    description="Average booking points per game (home)",
                    importance=0.3,
                ),
                ExplanationFactor(
                    name="Away Cards Avg", value=round(away.cards_for_avg, 2),
                    description="Average booking points per game (away)",
                    importance=0.3,
                ),
            ])
        return factors


# ────────────────────────────────────────────────────────────
# NBA regression model
# ────────────────────────────────────────────────────────────

HOME_ADVANTAGE_NBA = 2.5  # ~2.5 pts home advantage


class NBAModel:
    """Regression-based model for NBA markets."""

    def predict_team_points(
        self, home: TeamFeatures, away: TeamFeatures,
    ) -> tuple[float, float, float]:
        """Return (home_pts, away_pts, std_dev)."""
        # Pace-adjusted projection
        avg_pace = (home.pace + away.pace) / 2.0
        pace_factor = avg_pace / 100.0

        home_pts = (home.ortg * pace_factor + (100 - away.drtg) * pace_factor * 0.3) / 1.3
        away_pts = (away.ortg * pace_factor + (100 - home.drtg) * pace_factor * 0.3) / 1.3

        # Home advantage
        home_pts += HOME_ADVANTAGE_NBA / 2.0
        away_pts -= HOME_ADVANTAGE_NBA / 2.0

        # B2B adjustment
        if home.is_b2b:
            home_pts -= 2.0
        if away.is_b2b:
            away_pts -= 2.0

        # Form adjustment
        home_pts += (home.form_last5_win_pct - 0.5) * 3.0
        away_pts += (away.form_last5_win_pct - 0.5) * 3.0

        std = 12.0  # typical NBA game std dev
        return (max(85.0, home_pts), max(85.0, away_pts), std)

    def predict_moneyline(
        self, home: TeamFeatures, away: TeamFeatures,
    ) -> dict[str, float]:
        h_pts, a_pts, std = self.predict_team_points(home, away)
        diff = h_pts - a_pts
        p_home = norm_over(0, diff, std)
        return {"home": p_home, "away": 1.0 - p_home}

    def predict_spread(
        self, home: TeamFeatures, away: TeamFeatures, line: float,
    ) -> dict[str, float]:
        h_pts, a_pts, std = self.predict_team_points(home, away)
        diff = h_pts - a_pts
        # line is from home perspective: home -5.5 means home needs to win by 6+
        p_cover = norm_over(-line, diff, std)
        return {"home": p_cover, "away": 1.0 - p_cover}

    def predict_totals(
        self, home: TeamFeatures, away: TeamFeatures, line: float,
    ) -> dict[str, float]:
        h_pts, a_pts, std = self.predict_team_points(home, away)
        total = h_pts + a_pts
        combined_std = std * math.sqrt(2) * 0.85  # correlated
        return {
            "over": norm_over(line, total, combined_std),
            "under": norm_under(line, total, combined_std),
        }

    def predict_team_total(
        self, home: TeamFeatures, away: TeamFeatures, side: str, line: float,
    ) -> dict[str, float]:
        h_pts, a_pts, std = self.predict_team_points(home, away)
        pts = h_pts if side == "home" else a_pts
        return {
            "over": norm_over(line, pts, std),
            "under": norm_under(line, pts, std),
        }

    def predict_player_prop(
        self, player: PlayerFeatures, opponent: TeamFeatures,
        prop_type: str, line: float,
    ) -> dict[str, float]:
        """Predict player prop O/U."""
        stat_map = {
            "points": player.points_avg,
            "rebounds": player.rebounds_avg,
            "assists": player.assists_avg,
            "threes": player.threes_avg,
            "steals": player.steals_avg,
            "blocks": player.blocks_avg,
            "turnovers": player.turnovers_avg,
            "pra": player.pra_avg,
            "pr": player.points_avg + player.rebounds_avg,
            "pa": player.points_avg + player.assists_avg,
            "ra": player.rebounds_avg + player.assists_avg,
        }
        mu = stat_map.get(prop_type, 10.0)

        # Minutes adjustment
        if player.minutes_avg > 0:
            min_factor = player.minutes_avg / 32.0  # normalize to ~32 min
            mu *= min(1.2, max(0.7, min_factor))

        # Opponent adjustment for points
        if prop_type in ("points", "pra", "pr", "pa"):
            opp_drtg_diff = (opponent.drtg - 110.0) / 110.0
            mu *= (1.0 + opp_drtg_diff * 0.15)

        # For count stats use Poisson, for larger values use normal
        if mu < 5.0:
            return {
                "over": poisson_over(line, mu),
                "under": poisson_under(line, mu),
            }
        else:
            std = max(mu * 0.35, 3.0)
            return {
                "over": norm_over(line, mu, std),
                "under": norm_under(line, mu, std),
            }

    def predict_double_double(
        self, player: PlayerFeatures,
    ) -> dict[str, float]:
        """Heuristic for double-double probability."""
        cats = [player.points_avg, player.rebounds_avg, player.assists_avg]
        cats_above = sum(1 for c in cats if c >= 10.0)
        if cats_above >= 2:
            base = 0.45
        elif cats_above == 1:
            # Check how close others are
            close = sum(1 for c in cats if 7.0 <= c < 10.0)
            base = 0.15 + close * 0.12
        else:
            base = 0.05
        return {"yes": min(0.9, base), "no": max(0.1, 1.0 - base)}

    def predict_triple_double(
        self, player: PlayerFeatures,
    ) -> dict[str, float]:
        cats = [player.points_avg, player.rebounds_avg, player.assists_avg]
        cats_above = sum(1 for c in cats if c >= 10.0)
        if cats_above >= 3:
            base = 0.15
        elif cats_above == 2:
            base = 0.04
        else:
            base = 0.01
        return {"yes": min(0.5, base), "no": max(0.5, 1.0 - base)}

    def get_factors(
        self, home: TeamFeatures, away: TeamFeatures,
        player: PlayerFeatures | None = None, market_group: str = "",
    ) -> list[ExplanationFactor]:
        h_pts, a_pts, std = self.predict_team_points(home, away)
        factors = [
            ExplanationFactor(
                name="Home Projected Pts", value=round(h_pts, 1),
                description="Model projected points for home team",
                importance=0.25,
            ),
            ExplanationFactor(
                name="Away Projected Pts", value=round(a_pts, 1),
                description="Model projected points for away team",
                importance=0.25,
            ),
            ExplanationFactor(
                name="Pace Factor", value=round((home.pace + away.pace) / 2, 1),
                description="Average pace (possessions per game)",
                importance=0.2,
            ),
            ExplanationFactor(
                name="Home ORtg", value=round(home.ortg, 1),
                description="Home offensive rating",
                importance=0.15,
            ),
            ExplanationFactor(
                name="Away DRtg", value=round(away.drtg, 1),
                description="Away defensive rating",
                importance=0.15,
            ),
        ]
        if player:
            factors.append(ExplanationFactor(
                name="Player Avg", value=round(player.pra_avg, 1),
                description=f"Player PRA average (last N games)",
                importance=0.3,
            ))
        return factors


# ────────────────────────────────────────────────────────────
# NHL Poisson model
# ────────────────────────────────────────────────────────────

HOME_ADVANTAGE_NHL = 0.15


class NHLModel:
    """Poisson model for NHL markets."""

    def predict_lambdas(
        self, home: TeamFeatures, away: TeamFeatures,
    ) -> tuple[float, float]:
        league_avg = 3.1  # goals per game per team ~3.1 total each side

        # Shot-based approach: goals = shots * shooting_pct
        home_shooting = 1.0 - away.goalie_save_pct if away.goalie_save_pct > 0 else 0.09
        away_shooting = 1.0 - home.goalie_save_pct if home.goalie_save_pct > 0 else 0.09

        home_lam = home.shots_for_avg_nhl * home_shooting
        away_lam = away.shots_for_avg_nhl * away_shooting

        # Blend with average
        home_lam = 0.7 * home_lam + 0.3 * (league_avg / 2)
        away_lam = 0.7 * away_lam + 0.3 * (league_avg / 2)

        # Home advantage
        home_lam += HOME_ADVANTAGE_NHL
        away_lam -= HOME_ADVANTAGE_NHL * 0.5

        # Special teams adjustment
        pp_factor_h = (home.pp_pct - 0.2) * 0.5
        pp_factor_a = (away.pp_pct - 0.2) * 0.5
        home_lam += pp_factor_h
        away_lam += pp_factor_a

        home_lam = max(1.5, home_lam)
        away_lam = max(1.5, away_lam)
        return (home_lam, away_lam)

    def predict_moneyline(
        self, home: TeamFeatures, away: TeamFeatures,
    ) -> dict[str, float]:
        """Moneyline including OT/SO."""
        h_lam, a_lam = self.predict_lambdas(home, away)
        matrix = build_score_matrix(h_lam, a_lam, max_goals=10)
        reg_home = sum(matrix[i][j] for i in range(11) for j in range(i))
        reg_draw = sum(matrix[i][i] for i in range(11))
        reg_away = sum(matrix[i][j] for i in range(11) for j in range(i + 1, 11))
        # In OT, roughly 50/50 with slight home edge
        ot_home = reg_draw * 0.52
        ot_away = reg_draw * 0.48
        total_home = reg_home + ot_home
        total_away = reg_away + ot_away
        total = total_home + total_away
        return {"home": total_home / total, "away": total_away / total}

    def predict_regulation_time(
        self, home: TeamFeatures, away: TeamFeatures,
    ) -> dict[str, float]:
        h_lam, a_lam = self.predict_lambdas(home, away)
        matrix = build_score_matrix(h_lam, a_lam, max_goals=10)
        home_win = sum(matrix[i][j] for i in range(11) for j in range(i))
        draw = sum(matrix[i][i] for i in range(11))
        away_win = sum(matrix[i][j] for i in range(11) for j in range(i + 1, 11))
        total = home_win + draw + away_win
        return {"home": home_win / total, "draw": draw / total, "away": away_win / total}

    def predict_totals(
        self, home: TeamFeatures, away: TeamFeatures, line: float,
    ) -> dict[str, float]:
        h_lam, a_lam = self.predict_lambdas(home, away)
        total_lam = h_lam + a_lam
        return {"over": poisson_over(line, total_lam), "under": poisson_under(line, total_lam)}

    def predict_team_totals(
        self, home: TeamFeatures, away: TeamFeatures, side: str, line: float,
    ) -> dict[str, float]:
        h_lam, a_lam = self.predict_lambdas(home, away)
        lam = h_lam if side == "home" else a_lam
        return {"over": poisson_over(line, lam), "under": poisson_under(line, lam)}

    def predict_player_sog(
        self, player: PlayerFeatures, line: float,
    ) -> dict[str, float]:
        lam = player.sog_avg if player.sog_avg > 0 else 2.5
        return {"over": poisson_over(line, lam), "under": poisson_under(line, lam)}

    def predict_goalie_saves(
        self, player: PlayerFeatures, opponent: TeamFeatures, line: float,
    ) -> dict[str, float]:
        expected_shots = opponent.shots_for_avg_nhl
        save_pct = 0.91  # use player's if available
        if player.saves_avg > 0:
            save_pct = player.saves_avg / max(expected_shots, 25)
        expected_saves = expected_shots * save_pct
        std = max(expected_saves * 0.2, 4.0)
        return {
            "over": norm_over(line, expected_saves, std),
            "under": norm_under(line, expected_saves, std),
        }

    def predict_anytime_scorer(
        self, player: PlayerFeatures,
    ) -> dict[str, float]:
        lam = player.goals_avg if player.goals_avg > 0 else 0.15
        p = 1.0 - poisson_pmf(0, lam)
        return {"yes": p, "no": 1.0 - p}

    def get_factors(
        self, home: TeamFeatures, away: TeamFeatures,
        player: PlayerFeatures | None = None,
    ) -> list[ExplanationFactor]:
        h_lam, a_lam = self.predict_lambdas(home, away)
        factors = [
            ExplanationFactor(
                name="Home xG", value=round(h_lam, 3),
                description="Expected goals for home team",
                importance=0.25,
            ),
            ExplanationFactor(
                name="Away xG", value=round(a_lam, 3),
                description="Expected goals for away team",
                importance=0.25,
            ),
            ExplanationFactor(
                name="Home Shots/Game", value=round(home.shots_for_avg_nhl, 1),
                description="Home team shots per game average",
                importance=0.2,
            ),
            ExplanationFactor(
                name="Away Save%", value=round(away.goalie_save_pct, 3),
                description="Away goalie save percentage",
                importance=0.15,
            ),
            ExplanationFactor(
                name="Home PP%", value=round(home.pp_pct, 3),
                description="Home powerplay percentage",
                importance=0.15,
            ),
        ]
        if player:
            factors.append(ExplanationFactor(
                name="Player SOG Avg", value=round(player.sog_avg, 2),
                description="Player shots on goal average",
                importance=0.3,
            ))
        return factors


# ────────────────────────────────────────────────────────────
# Tennis ELO model
# ────────────────────────────────────────────────────────────

class TennisModel:
    """ELO-based model for tennis markets."""

    def predict_match_winner(
        self, home: TeamFeatures, away: TeamFeatures,
    ) -> dict[str, float]:
        """Home = Player 1 (listed first), Away = Player 2."""
        # Weighted blend: 70% surface ELO, 30% overall ELO
        p1_elo = 0.7 * home.elo_surface + 0.3 * home.elo_overall
        p2_elo = 0.7 * away.elo_surface + 0.3 * away.elo_overall

        # Form adjustment
        form_adj = (home.form_last5_win_pct - away.form_last5_win_pct) * 50
        p1_elo += form_adj

        p1_win = elo_win_prob(p1_elo, p2_elo)
        return {"home": p1_win, "away": 1.0 - p1_win}

    def predict_set_betting(
        self, home: TeamFeatures, away: TeamFeatures, best_of: int = 3,
    ) -> list[dict]:
        """Predict exact set score probabilities."""
        p = self.predict_match_winner(home, away)["home"]
        q = 1.0 - p

        # Set win probability (simplified)
        p_set = 0.5 + (p - 0.5) * 0.8  # dampen match prob for set level

        results = []
        if best_of == 3:
            p_20 = p_set ** 2
            p_21 = 2 * p_set ** 2 * (1 - p_set)
            p_02 = (1 - p_set) ** 2
            p_12 = 2 * (1 - p_set) ** 2 * p_set
            total = p_20 + p_21 + p_02 + p_12
            results = [
                {"label": "2-0", "prob": p_20 / total},
                {"label": "2-1", "prob": p_21 / total},
                {"label": "0-2", "prob": p_02 / total},
                {"label": "1-2", "prob": p_12 / total},
            ]
        else:  # best of 5
            # Simplified using binomial-like
            p_30 = p_set ** 3
            p_31 = 3 * p_set ** 3 * (1 - p_set)
            p_32 = 6 * p_set ** 3 * (1 - p_set) ** 2
            p_03 = (1 - p_set) ** 3
            p_13 = 3 * (1 - p_set) ** 3 * p_set
            p_23 = 6 * (1 - p_set) ** 3 * p_set ** 2
            total = p_30 + p_31 + p_32 + p_03 + p_13 + p_23
            results = [
                {"label": "3-0", "prob": p_30 / total},
                {"label": "3-1", "prob": p_31 / total},
                {"label": "3-2", "prob": p_32 / total},
                {"label": "0-3", "prob": p_03 / total},
                {"label": "1-3", "prob": p_13 / total},
                {"label": "2-3", "prob": p_23 / total},
            ]
        results.sort(key=lambda x: x["prob"], reverse=True)
        return results

    def predict_total_games(
        self, home: TeamFeatures, away: TeamFeatures, line: float,
    ) -> dict[str, float]:
        """Total games approximated via expected sets and games per set."""
        p = self.predict_match_winner(home, away)["home"]
        closeness = 1.0 - abs(p - 0.5) * 2  # 0=dominant, 1=even
        # Expected games: close match ~24-26, dominant ~18-20
        expected_games = 18.0 + closeness * 7.0
        # Serve quality increases hold rates, potentially more games
        serve_factor = (home.hold_pct + away.hold_pct) / 2.0
        expected_games += (serve_factor - 0.75) * 5.0
        std = 4.0
        return {
            "over": norm_over(line, expected_games, std),
            "under": norm_under(line, expected_games, std),
        }

    def predict_tiebreak(
        self, home: TeamFeatures, away: TeamFeatures,
    ) -> dict[str, float]:
        closeness = 1.0 - abs(
            self.predict_match_winner(home, away)["home"] - 0.5
        ) * 2
        serve_quality = (home.hold_pct + away.hold_pct) / 2.0
        # Higher serve quality + close match = more tiebreaks
        p_tb = 0.2 + closeness * 0.3 + (serve_quality - 0.75) * 0.4
        p_tb = max(0.1, min(0.7, p_tb))
        return {"yes": p_tb, "no": 1.0 - p_tb}

    def predict_player_aces(
        self, player: PlayerFeatures, line: float,
    ) -> dict[str, float]:
        lam = player.extra.get("aces_per_match", 5.0)
        return {"over": poisson_over(line, lam), "under": poisson_under(line, lam)}

    def get_factors(
        self, home: TeamFeatures, away: TeamFeatures,
    ) -> list[ExplanationFactor]:
        return [
            ExplanationFactor(
                name="P1 Surface ELO", value=round(home.elo_surface, 0),
                description="Player 1 ELO on this surface",
                importance=0.3,
            ),
            ExplanationFactor(
                name="P2 Surface ELO", value=round(away.elo_surface, 0),
                description="Player 2 ELO on this surface",
                importance=0.3,
            ),
            ExplanationFactor(
                name="P1 Hold%", value=round(home.hold_pct, 3),
                description="Player 1 service hold percentage",
                importance=0.15,
            ),
            ExplanationFactor(
                name="P2 Break%", value=round(away.break_pct, 3),
                description="Player 2 return break percentage",
                importance=0.15,
            ),
            ExplanationFactor(
                name="P1 Form (L5)", value=round(home.form_last5_win_pct, 3),
                description="Player 1 win rate last 5 matches",
                importance=0.1,
            ),
        ]
