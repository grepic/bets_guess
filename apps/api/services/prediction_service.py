"""Main prediction service - orchestrates feature building and model inference."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from packages.shared.enums.market import (
    BetTag, MarketGroup, MarketType, OutcomeType, Period, RiskLevel, Side,
)
from packages.shared.enums.sport import League, Sport
from packages.shared.schemas.game import FilterParams, GameInfo, OddsSnapshot
from packages.shared.schemas.market import (
    BestBet, ExplanationFactor, MarketSpec, PredictionResult,
)
from packages.shared.catalog.registry import MarketRegistry, get_registry
from apps.api.providers.base import OddsProvider, ScheduleProvider, StatsProvider
from apps.api.services.features import (
    TeamFeatures, PlayerFeatures,
    compute_player_features, compute_team_features,
)
from apps.api.services.prediction_models import (
    NBAModel, NHLModel, SoccerPoissonModel, TennisModel,
    confidence_interval,
)


class PredictionService:
    """Orchestrates predictions across all sports and market types."""

    def __init__(
        self,
        schedule: ScheduleProvider,
        stats: StatsProvider,
        odds: OddsProvider,
    ) -> None:
        self.schedule = schedule
        self.stats = stats
        self.odds = odds
        self.registry: MarketRegistry = get_registry()
        self.soccer_model = SoccerPoissonModel()
        self.nba_model = NBAModel()
        self.nhl_model = NHLModel()
        self.tennis_model = TennisModel()

    async def _build_team_features(
        self, team_id: str, sport: Sport, is_home: bool,
    ) -> TeamFeatures:
        game_stats = await self.stats.get_team_stats(team_id, last_n=10)
        season_stats = await self.stats.get_team_season_stats(team_id, "current")
        return compute_team_features(team_id, sport, is_home, game_stats, season_stats)

    async def _build_player_features(
        self, player_id: str, team_id: str, sport: Sport,
    ) -> PlayerFeatures:
        game_stats = await self.stats.get_player_stats(player_id, last_n=10)
        return compute_player_features(player_id, team_id, sport, game_stats)

    def _make_prediction(
        self, game_id: str, spec: MarketSpec,
        outcome: OutcomeType, label: str,
        prob: float, factors: list[ExplanationFactor],
        sample_size: int = 50,
    ) -> PredictionResult:
        prob = max(0.001, min(0.999, prob))
        fair_odds = round(1.0 / prob, 3)
        low, high = confidence_interval(prob, sample_size)
        return PredictionResult(
            game_id=game_id,
            market_spec=spec,
            outcome=outcome,
            outcome_label=label,
            probability=round(prob, 4),
            fair_odds=fair_odds,
            interval_low=low,
            interval_high=high,
            factors=factors,
        )

    async def predict_game(
        self, game: GameInfo,
        market_groups: list[MarketGroup] | None = None,
    ) -> list[PredictionResult]:
        """Generate predictions for all requested markets in a game."""
        sport = game.sport
        available = self.registry.list_for_sport(sport)

        if market_groups:
            available = [d for d in available if d.market_group in market_groups]

        home_feats = await self._build_team_features(
            game.home_team.team_id, sport, is_home=True,
        )
        away_feats = await self._build_team_features(
            game.away_team.team_id, sport, is_home=False,
        )

        predictions: list[PredictionResult] = []

        for defn in available:
            mg = defn.market_group
            try:
                preds = await self._predict_market(
                    game.game_id, sport, mg, defn,
                    home_feats, away_feats,
                )
                predictions.extend(preds)
            except Exception:
                continue  # Skip markets that fail gracefully

        return predictions

    async def _predict_market(
        self, game_id: str, sport: Sport, mg: MarketGroup,
        defn: Any, home: TeamFeatures, away: TeamFeatures,
    ) -> list[PredictionResult]:
        """Route to correct model based on sport and market group."""
        results: list[PredictionResult] = []

        if sport == Sport.SOCCER:
            results = self._predict_soccer_market(game_id, mg, defn, home, away)
        elif sport == Sport.NBA:
            results = self._predict_nba_market(game_id, mg, defn, home, away)
        elif sport == Sport.NHL:
            results = self._predict_nhl_market(game_id, mg, defn, home, away)
        elif sport == Sport.TENNIS:
            results = self._predict_tennis_market(game_id, mg, defn, home, away)

        return results

    def _predict_soccer_market(
        self, game_id: str, mg: MarketGroup, defn: Any,
        home: TeamFeatures, away: TeamFeatures,
    ) -> list[PredictionResult]:
        results: list[PredictionResult] = []
        m = self.soccer_model
        factors = m.get_factors(home, away, mg.value)

        if mg in (MarketGroup.SOCCER_1X2_FT, MarketGroup.SOCCER_1X2_HT):
            probs = m.predict_1x2(home, away)
            period = Period.FULL_TIME if mg == MarketGroup.SOCCER_1X2_FT else Period.FIRST_HALF
            # Half-time: dampen probabilities (more draws)
            if period == Period.FIRST_HALF:
                draw_boost = 0.1
                probs["draw"] += draw_boost
                probs["home"] -= draw_boost / 2
                probs["away"] -= draw_boost / 2

            for outcome_key, label in [("home", "Home"), ("draw", "Draw"), ("away", "Away")]:
                ot = {"home": OutcomeType.HOME, "draw": OutcomeType.DRAW, "away": OutcomeType.AWAY}[outcome_key]
                spec = MarketSpec(market_group=mg, market_type=MarketType.RESULT, period=period)
                results.append(self._make_prediction(game_id, spec, ot, label, probs[outcome_key], factors))

        elif mg == MarketGroup.DOUBLE_CHANCE:
            probs = m.predict_1x2(home, away)
            for label, prob in [
                ("1X", probs["home"] + probs["draw"]),
                ("12", probs["home"] + probs["away"]),
                ("X2", probs["draw"] + probs["away"]),
            ]:
                spec = MarketSpec(market_group=mg, market_type=MarketType.RESULT)
                ot = {"1X": OutcomeType.HOME, "12": OutcomeType.DRAW, "X2": OutcomeType.AWAY}[label]
                results.append(self._make_prediction(game_id, spec, ot, label, prob, factors))

        elif mg == MarketGroup.DRAW_NO_BET:
            probs = m.predict_1x2(home, away)
            total_no_draw = probs["home"] + probs["away"]
            if total_no_draw > 0:
                for label, prob in [("Home", probs["home"] / total_no_draw), ("Away", probs["away"] / total_no_draw)]:
                    spec = MarketSpec(market_group=mg, market_type=MarketType.RESULT)
                    ot = OutcomeType.HOME if label == "Home" else OutcomeType.AWAY
                    results.append(self._make_prediction(game_id, spec, ot, label, prob, factors))

        elif mg == MarketGroup.TOTALS:
            for line in defn.default_lines:
                probs = m.predict_totals(home, away, line)
                for ot_key, label in [("over", f"Over {line}"), ("under", f"Under {line}")]:
                    ot = OutcomeType.OVER if ot_key == "over" else OutcomeType.UNDER
                    spec = MarketSpec(market_group=mg, market_type=MarketType.TOTALS, line_value=line, line_unit=defn.line_unit)
                    results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], factors))

        elif mg == MarketGroup.TEAM_TOTALS:
            for side_val in ("home", "away"):
                for line in defn.default_lines:
                    probs = m.predict_team_totals(home, away, side_val, line)
                    side = Side.HOME if side_val == "home" else Side.AWAY
                    for ot_key, label in [("over", f"{side_val.title()} Over {line}"), ("under", f"{side_val.title()} Under {line}")]:
                        ot = OutcomeType.OVER if ot_key == "over" else OutcomeType.UNDER
                        spec = MarketSpec(market_group=mg, market_type=MarketType.TEAM_TOTALS, side=side, line_value=line, line_unit=defn.line_unit)
                        results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], factors))

        elif mg == MarketGroup.SOCCER_BTTS:
            probs = m.predict_btts(home, away)
            for ot_key, label in [("yes", "BTTS Yes"), ("no", "BTTS No")]:
                ot = OutcomeType.YES if ot_key == "yes" else OutcomeType.NO
                spec = MarketSpec(market_group=mg, market_type=MarketType.YES_NO)
                results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], factors))

        elif mg == MarketGroup.SOCCER_CLEAN_SHEET:
            for side_val in ("home", "away"):
                probs = m.predict_clean_sheet(home, away, side_val)
                side = Side.HOME if side_val == "home" else Side.AWAY
                for ot_key, label in [("yes", f"{side_val.title()} CS Yes"), ("no", f"{side_val.title()} CS No")]:
                    ot = OutcomeType.YES if ot_key == "yes" else OutcomeType.NO
                    spec = MarketSpec(market_group=mg, market_type=MarketType.YES_NO, side=side)
                    results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], factors))

        elif mg == MarketGroup.SOCCER_WIN_TO_NIL:
            for side_val in ("home", "away"):
                probs = m.predict_win_to_nil(home, away, side_val)
                side = Side.HOME if side_val == "home" else Side.AWAY
                for ot_key, label in [("yes", f"{side_val.title()} WTN Yes"), ("no", f"{side_val.title()} WTN No")]:
                    ot = OutcomeType.YES if ot_key == "yes" else OutcomeType.NO
                    spec = MarketSpec(market_group=mg, market_type=MarketType.YES_NO, side=side)
                    results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], factors))

        elif mg == MarketGroup.SOCCER_CORRECT_SCORE:
            scores = m.predict_correct_score(home, away)
            for s in scores:
                spec = MarketSpec(market_group=mg, market_type=MarketType.CORRECT_SCORE, bucket_label=s["label"])
                results.append(self._make_prediction(game_id, spec, OutcomeType.EXACT_SCORE, s["label"], s["prob"], factors))

        elif mg == MarketGroup.WINNING_MARGIN:
            margins = m.predict_winning_margin(home, away)
            for marg in margins:
                spec = MarketSpec(market_group=mg, market_type=MarketType.WINNING_MARGIN, bucket_label=marg["label"])
                results.append(self._make_prediction(game_id, spec, OutcomeType.BUCKET, marg["label"], marg["prob"], factors))

        elif mg == MarketGroup.SOCCER_CORNERS_TOTAL:
            corner_factors = m.get_factors(home, away, "corner")
            for line in defn.default_lines:
                probs = m.predict_corners_total(home, away, line)
                for ot_key, label in [("over", f"Corners Over {line}"), ("under", f"Corners Under {line}")]:
                    ot = OutcomeType.OVER if ot_key == "over" else OutcomeType.UNDER
                    spec = MarketSpec(market_group=mg, market_type=MarketType.TOTALS, line_value=line, line_unit=defn.line_unit)
                    results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], corner_factors))

        elif mg == MarketGroup.SOCCER_CORNERS_TEAM:
            corner_factors = m.get_factors(home, away, "corner")
            for side_val in ("home", "away"):
                for line in defn.default_lines:
                    probs = m.predict_corners_team(home, away, side_val, line)
                    side = Side.HOME if side_val == "home" else Side.AWAY
                    for ot_key, label in [("over", f"{side_val.title()} Corners O {line}"), ("under", f"{side_val.title()} Corners U {line}")]:
                        ot = OutcomeType.OVER if ot_key == "over" else OutcomeType.UNDER
                        spec = MarketSpec(market_group=mg, market_type=MarketType.TEAM_TOTALS, side=side, line_value=line, line_unit=defn.line_unit)
                        results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], corner_factors))

        elif mg == MarketGroup.SOCCER_CARDS_TOTAL:
            card_factors = m.get_factors(home, away, "card")
            for line in defn.default_lines:
                probs = m.predict_cards_total(home, away, line)
                for ot_key, label in [("over", f"Cards Over {line}"), ("under", f"Cards Under {line}")]:
                    ot = OutcomeType.OVER if ot_key == "over" else OutcomeType.UNDER
                    spec = MarketSpec(market_group=mg, market_type=MarketType.TOTALS, line_value=line, line_unit=defn.line_unit)
                    results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], card_factors))

        elif mg == MarketGroup.SOCCER_CARDS_TEAM:
            card_factors = m.get_factors(home, away, "card")
            for side_val in ("home", "away"):
                for line in defn.default_lines:
                    probs = m.predict_cards_team(home, away, side_val, line)
                    side = Side.HOME if side_val == "home" else Side.AWAY
                    for ot_key, label in [("over", f"{side_val.title()} Cards O {line}"), ("under", f"{side_val.title()} Cards U {line}")]:
                        ot = OutcomeType.OVER if ot_key == "over" else OutcomeType.UNDER
                        spec = MarketSpec(market_group=mg, market_type=MarketType.TEAM_TOTALS, side=side, line_value=line, line_unit=defn.line_unit)
                        results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], card_factors))

        elif mg == MarketGroup.SOCCER_RED_CARD:
            probs = m.predict_red_card(home, away)
            for ot_key, label in [("yes", "Red Card Yes"), ("no", "Red Card No")]:
                ot = OutcomeType.YES if ot_key == "yes" else OutcomeType.NO
                spec = MarketSpec(market_group=mg, market_type=MarketType.YES_NO)
                results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], factors))

        elif mg == MarketGroup.SOCCER_SHOTS_TOTAL:
            for line in defn.default_lines:
                probs = m.predict_shots_total(home, away, line)
                for ot_key, label in [("over", f"Shots Over {line}"), ("under", f"Shots Under {line}")]:
                    ot = OutcomeType.OVER if ot_key == "over" else OutcomeType.UNDER
                    spec = MarketSpec(market_group=mg, market_type=MarketType.TOTALS, line_value=line, line_unit=defn.line_unit)
                    results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], factors))

        elif mg == MarketGroup.SOCCER_SOT_TOTAL:
            for line in defn.default_lines:
                probs = m.predict_sot_total(home, away, line)
                for ot_key, label in [("over", f"SOT Over {line}"), ("under", f"SOT Under {line}")]:
                    ot = OutcomeType.OVER if ot_key == "over" else OutcomeType.UNDER
                    spec = MarketSpec(market_group=mg, market_type=MarketType.TOTALS, line_value=line, line_unit=defn.line_unit)
                    results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], factors))

        elif mg == MarketGroup.SPREAD:
            for line in defn.default_lines:
                h_lam, a_lam = m.predict_lambdas(home, away)
                matrix = build_score_matrix_for_spread(h_lam, a_lam, line)
                for ot_key, label in [("home", f"Home {line:+g}"), ("away", f"Away {-line:+g}")]:
                    ot = OutcomeType.HOME if ot_key == "home" else OutcomeType.AWAY
                    spec = MarketSpec(market_group=mg, market_type=MarketType.HANDICAP, line_value=line, line_unit=defn.line_unit)
                    results.append(self._make_prediction(game_id, spec, ot, label, matrix[ot_key], factors))

        return results

    def _predict_nba_market(
        self, game_id: str, mg: MarketGroup, defn: Any,
        home: TeamFeatures, away: TeamFeatures,
    ) -> list[PredictionResult]:
        results: list[PredictionResult] = []
        m = self.nba_model
        factors = m.get_factors(home, away)

        if mg == MarketGroup.NBA_MONEYLINE:
            probs = m.predict_moneyline(home, away)
            for ot_key, label in [("home", "Home"), ("away", "Away")]:
                ot = OutcomeType.HOME if ot_key == "home" else OutcomeType.AWAY
                spec = MarketSpec(market_group=mg, market_type=MarketType.RESULT)
                results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], factors))

        elif mg == MarketGroup.NBA_SPREAD:
            for line in defn.default_lines:
                probs = m.predict_spread(home, away, line)
                for ot_key, label in [("home", f"Home {line:+g}"), ("away", f"Away {-line:+g}")]:
                    ot = OutcomeType.HOME if ot_key == "home" else OutcomeType.AWAY
                    spec = MarketSpec(market_group=mg, market_type=MarketType.HANDICAP, line_value=line, line_unit=defn.line_unit)
                    results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], factors))

        elif mg == MarketGroup.NBA_TOTALS:
            for line in defn.default_lines:
                probs = m.predict_totals(home, away, line)
                for ot_key, label in [("over", f"Over {line}"), ("under", f"Under {line}")]:
                    ot = OutcomeType.OVER if ot_key == "over" else OutcomeType.UNDER
                    spec = MarketSpec(market_group=mg, market_type=MarketType.TOTALS, line_value=line, line_unit=defn.line_unit)
                    results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], factors))

        elif mg == MarketGroup.NBA_TEAM_TOTALS:
            for side_val in ("home", "away"):
                for line in defn.default_lines:
                    probs = m.predict_team_total(home, away, side_val, line)
                    side = Side.HOME if side_val == "home" else Side.AWAY
                    for ot_key, label in [("over", f"{side_val.title()} Over {line}"), ("under", f"{side_val.title()} Under {line}")]:
                        ot = OutcomeType.OVER if ot_key == "over" else OutcomeType.UNDER
                        spec = MarketSpec(market_group=mg, market_type=MarketType.TEAM_TOTALS, side=side, line_value=line, line_unit=defn.line_unit)
                        results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], factors))

        elif mg in (MarketGroup.NBA_1H_WINNER, MarketGroup.NBA_2H_WINNER):
            probs = m.predict_moneyline(home, away)
            # Dampen for half
            probs["home"] = 0.5 + (probs["home"] - 0.5) * 0.75
            probs["away"] = 1.0 - probs["home"]
            period = Period.FIRST_HALF if mg == MarketGroup.NBA_1H_WINNER else Period.SECOND_HALF
            for ot_key, label in [("home", "Home"), ("away", "Away")]:
                ot = OutcomeType.HOME if ot_key == "home" else OutcomeType.AWAY
                spec = MarketSpec(market_group=mg, market_type=MarketType.RESULT, period=period)
                results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], factors))

        elif mg == MarketGroup.NBA_1H_TOTALS:
            for line in defn.default_lines:
                h_pts, a_pts, std = m.predict_team_points(home, away)
                half_total = (h_pts + a_pts) * 0.50
                half_std = std * 0.75
                probs = {
                    "over": 1.0 - _norm_cdf_inline(line, half_total, half_std),
                    "under": _norm_cdf_inline(line, half_total, half_std),
                }
                for ot_key, label in [("over", f"1H Over {line}"), ("under", f"1H Under {line}")]:
                    ot = OutcomeType.OVER if ot_key == "over" else OutcomeType.UNDER
                    spec = MarketSpec(market_group=mg, market_type=MarketType.TOTALS, period=Period.FIRST_HALF, line_value=line, line_unit=defn.line_unit)
                    results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], factors))

        return results

    def _predict_nhl_market(
        self, game_id: str, mg: MarketGroup, defn: Any,
        home: TeamFeatures, away: TeamFeatures,
    ) -> list[PredictionResult]:
        results: list[PredictionResult] = []
        m = self.nhl_model
        factors = m.get_factors(home, away)

        if mg == MarketGroup.NHL_MONEYLINE:
            probs = m.predict_moneyline(home, away)
            for ot_key, label in [("home", "Home"), ("away", "Away")]:
                ot = OutcomeType.HOME if ot_key == "home" else OutcomeType.AWAY
                spec = MarketSpec(market_group=mg, market_type=MarketType.RESULT)
                results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], factors))

        elif mg == MarketGroup.NHL_REG_TIME:
            probs = m.predict_regulation_time(home, away)
            for ot_key, label in [("home", "Home"), ("draw", "Draw"), ("away", "Away")]:
                ot = {"home": OutcomeType.HOME, "draw": OutcomeType.DRAW, "away": OutcomeType.AWAY}[ot_key]
                spec = MarketSpec(market_group=mg, market_type=MarketType.RESULT, period=Period.REGULATION)
                results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], factors))

        elif mg == MarketGroup.NHL_TOTALS:
            for line in defn.default_lines:
                probs = m.predict_totals(home, away, line)
                for ot_key, label in [("over", f"Over {line}"), ("under", f"Under {line}")]:
                    ot = OutcomeType.OVER if ot_key == "over" else OutcomeType.UNDER
                    spec = MarketSpec(market_group=mg, market_type=MarketType.TOTALS, line_value=line, line_unit=defn.line_unit)
                    results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], factors))

        elif mg == MarketGroup.NHL_TEAM_TOTALS:
            for side_val in ("home", "away"):
                for line in defn.default_lines:
                    probs = m.predict_team_totals(home, away, side_val, line)
                    side = Side.HOME if side_val == "home" else Side.AWAY
                    for ot_key, label in [("over", f"{side_val.title()} Over {line}"), ("under", f"{side_val.title()} Under {line}")]:
                        ot = OutcomeType.OVER if ot_key == "over" else OutcomeType.UNDER
                        spec = MarketSpec(market_group=mg, market_type=MarketType.TEAM_TOTALS, side=side, line_value=line, line_unit=defn.line_unit)
                        results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], factors))

        elif mg == MarketGroup.NHL_PUCK_LINE:
            for line in defn.default_lines:
                probs = m.predict_totals(home, away, abs(line))  # simplified
                for ot_key, label in [("home", f"Home {line:+g}"), ("away", f"Away {-line:+g}")]:
                    ot = OutcomeType.HOME if ot_key == "home" else OutcomeType.AWAY
                    spec = MarketSpec(market_group=mg, market_type=MarketType.HANDICAP, line_value=line, line_unit=defn.line_unit)
                    prob = probs["over"] if (ot_key == "home" and line < 0) else probs["under"]
                    results.append(self._make_prediction(game_id, spec, ot, label, prob, factors))

        return results

    def _predict_tennis_market(
        self, game_id: str, mg: MarketGroup, defn: Any,
        home: TeamFeatures, away: TeamFeatures,
    ) -> list[PredictionResult]:
        results: list[PredictionResult] = []
        m = self.tennis_model
        factors = m.get_factors(home, away)

        if mg == MarketGroup.TENNIS_WINNER:
            probs = m.predict_match_winner(home, away)
            for ot_key, label in [("home", "Player 1"), ("away", "Player 2")]:
                ot = OutcomeType.HOME if ot_key == "home" else OutcomeType.AWAY
                spec = MarketSpec(market_group=mg, market_type=MarketType.RESULT)
                results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], factors))

        elif mg == MarketGroup.TENNIS_SET_BETTING:
            scores = m.predict_set_betting(home, away)
            for s in scores:
                spec = MarketSpec(market_group=mg, market_type=MarketType.CORRECT_SCORE, bucket_label=s["label"])
                results.append(self._make_prediction(game_id, spec, OutcomeType.EXACT_SCORE, s["label"], s["prob"], factors))

        elif mg == MarketGroup.TENNIS_TOTAL_GAMES:
            for line in defn.default_lines:
                probs = m.predict_total_games(home, away, line)
                for ot_key, label in [("over", f"Games Over {line}"), ("under", f"Games Under {line}")]:
                    ot = OutcomeType.OVER if ot_key == "over" else OutcomeType.UNDER
                    spec = MarketSpec(market_group=mg, market_type=MarketType.TOTALS, line_value=line, line_unit=defn.line_unit)
                    results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], factors))

        elif mg == MarketGroup.TENNIS_TIEBREAK:
            probs = m.predict_tiebreak(home, away)
            for ot_key, label in [("yes", "Tiebreak Yes"), ("no", "Tiebreak No")]:
                ot = OutcomeType.YES if ot_key == "yes" else OutcomeType.NO
                spec = MarketSpec(market_group=mg, market_type=MarketType.YES_NO)
                results.append(self._make_prediction(game_id, spec, ot, label, probs[ot_key], factors))

        elif mg == MarketGroup.TENNIS_FIRST_SET:
            probs = m.predict_match_winner(home, away)
            # First set is slightly correlated with match winner but less decisive
            p1 = 0.5 + (probs["home"] - 0.5) * 0.85
            for ot_key, label, prob in [("home", "P1 1st Set", p1), ("away", "P2 1st Set", 1.0 - p1)]:
                ot = OutcomeType.HOME if ot_key == "home" else OutcomeType.AWAY
                spec = MarketSpec(market_group=mg, market_type=MarketType.RESULT, period=Period.SET_1)
                results.append(self._make_prediction(game_id, spec, ot, label, prob, factors))

        elif mg == MarketGroup.TENNIS_SET_TOTALS:
            for line in defn.default_lines:
                probs = m.predict_set_betting(home, away)
                # Over 2.5 sets = probability of 3-set match
                three_set_prob = sum(s["prob"] for s in probs if "1" in s["label"].split("-"))
                if line == 2.5:
                    o_prob = three_set_prob
                else:
                    o_prob = 0.5
                spec = MarketSpec(market_group=mg, market_type=MarketType.TOTALS, line_value=line, line_unit=defn.line_unit)
                results.append(self._make_prediction(game_id, spec, OutcomeType.OVER, f"Sets Over {line}", o_prob, factors))
                results.append(self._make_prediction(game_id, spec, OutcomeType.UNDER, f"Sets Under {line}", 1.0 - o_prob, factors))

        return results

    async def generate_best_bets(
        self, filters: FilterParams,
    ) -> list[BestBet]:
        """Find all value bets matching filter criteria."""
        games = await self.schedule.get_games(
            sport=filters.sport or Sport.SOCCER,
            game_date=filters.date,
        )
        if filters.sport is None:
            # Get all sports
            all_games: list[GameInfo] = []
            for s in Sport:
                sg = await self.schedule.get_games(sport=s, game_date=filters.date)
                all_games.extend(sg)
            games = all_games

        market_groups = None
        if filters.market_group:
            market_groups = [filters.market_group]

        best_bets: list[BestBet] = []
        for game in games:
            predictions = await self.predict_game(game, market_groups)
            odds_list = await self.odds.get_odds(game.game_id)

            odds_map: dict[str, OddsSnapshot] = {}
            for o in odds_list:
                key = f"{o.market_key}:{o.outcome_label}"
                if key not in odds_map or o.price > odds_map[key].price:
                    odds_map[key] = o

            for pred in predictions:
                odds_key = f"{pred.market_spec.normalized_key}:{pred.outcome_label}"
                odds_snap = odds_map.get(odds_key)

                if not odds_snap and filters.hide_missing_odds:
                    continue

                book_odds = odds_snap.price if odds_snap else pred.fair_odds
                implied_prob = 1.0 / book_odds if book_odds > 0 else 0.0
                edge = ((pred.probability - implied_prob) / implied_prob * 100) if implied_prob > 0 else 0.0

                if edge < filters.min_edge:
                    continue
                if pred.probability < filters.min_probability:
                    continue
                if filters.min_confidence > 0 and pred.interval_low < filters.min_confidence:
                    continue

                # Determine tag
                tag = BetTag.VALUE
                if pred.probability > 0.65 and edge > 5:
                    tag = BetTag.HIGH_CONF
                elif pred.probability < 0.15 and edge > 10:
                    tag = BetTag.LONGSHOT

                # Risk assessment
                risk = RiskLevel.MEDIUM
                risk_note = ""
                if pred.probability < 0.2:
                    risk = RiskLevel.HIGH
                    risk_note = "Low probability market - high variance"
                elif pred.probability > 0.7:
                    risk = RiskLevel.LOW

                defn = self.registry.get(pred.market_spec.market_group)
                market_name = defn.display_name if defn else pred.market_spec.market_group.value

                best_bets.append(BestBet(
                    game_id=game.game_id,
                    sport=game.sport,
                    league=game.league,
                    home_team=game.home_team.name,
                    away_team=game.away_team.name,
                    start_time=game.start_time,
                    market_name=market_name,
                    market_spec=pred.market_spec,
                    outcome=pred.outcome,
                    outcome_label=pred.outcome_label,
                    bookmaker_odds=book_odds,
                    implied_prob=round(implied_prob, 4),
                    model_prob=pred.probability,
                    fair_odds=pred.fair_odds,
                    edge_pct=round(edge, 2),
                    interval_low=pred.interval_low,
                    interval_high=pred.interval_high,
                    factors=pred.factors,
                    risk_note=risk_note,
                    risk_level=risk,
                    tag=tag,
                ))

        best_bets.sort(key=lambda b: b.edge_pct, reverse=True)
        return best_bets[:filters.limit]


def build_score_matrix_for_spread(h_lam: float, a_lam: float, line: float) -> dict[str, float]:
    """For soccer spread markets."""
    from apps.api.services.prediction_models import build_score_matrix
    matrix = build_score_matrix(h_lam, a_lam)
    home_cover = 0.0
    away_cover = 0.0
    for i in range(9):
        for j in range(9):
            diff = i - j + line
            if diff > 0:
                home_cover += matrix[i][j]
            elif diff < 0:
                away_cover += matrix[i][j]
            else:
                home_cover += matrix[i][j] / 2
                away_cover += matrix[i][j] / 2
    total = home_cover + away_cover
    return {"home": home_cover / total if total > 0 else 0.5, "away": away_cover / total if total > 0 else 0.5}


def _norm_cdf_inline(x: float, mu: float, sigma: float) -> float:
    import math
    if sigma <= 0:
        return 1.0 if x >= mu else 0.0
    return 0.5 * (1.0 + math.erf((x - mu) / (sigma * math.sqrt(2))))
