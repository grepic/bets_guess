"""Rules Engine for bet builder compatibility and correlation adjustments."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from packages.shared.enums.market import (
    CorrelationCategory, MarketGroup, MarketType, OutcomeType, RiskLevel,
)
from packages.shared.schemas.market import (
    BetBuilderLeg, BetBuilderProposal, MarketSpec, PredictionResult,
)
from packages.shared.catalog.registry import get_registry


# ────────────────────────────────────────────────────────────
# Incompatibility rules
# ────────────────────────────────────────────────────────────

# Pairs of market groups that CANNOT coexist in a bet builder
INCOMPATIBLE_PAIRS: set[frozenset[MarketGroup]] = {
    # Correct score conflicts with specific totals
    frozenset({MarketGroup.SOCCER_CORRECT_SCORE, MarketGroup.TOTALS}),
    frozenset({MarketGroup.SOCCER_CORRECT_SCORE, MarketGroup.TEAM_TOTALS}),
    frozenset({MarketGroup.SOCCER_CORRECT_SCORE, MarketGroup.SOCCER_BTTS}),
    frozenset({MarketGroup.SOCCER_CORRECT_SCORE, MarketGroup.SOCCER_CLEAN_SHEET}),
    frozenset({MarketGroup.SOCCER_CORRECT_SCORE, MarketGroup.SOCCER_WIN_TO_NIL}),
    frozenset({MarketGroup.SOCCER_CORRECT_SCORE, MarketGroup.WINNING_MARGIN}),
    # Result + DNB conflict
    frozenset({MarketGroup.SOCCER_1X2_FT, MarketGroup.DRAW_NO_BET}),
    frozenset({MarketGroup.SOCCER_1X2_FT, MarketGroup.DOUBLE_CHANCE}),
    # Win to nil + BTTS
    frozenset({MarketGroup.SOCCER_WIN_TO_NIL, MarketGroup.SOCCER_BTTS}),
    # NBA: moneyline + spread cover same outcome
    frozenset({MarketGroup.NBA_MONEYLINE, MarketGroup.NBA_SPREAD}),
    # NHL: moneyline + reg time (overlapping)
    frozenset({MarketGroup.NHL_MONEYLINE, MarketGroup.NHL_REG_TIME}),
    # Tennis: winner + first set (high overlap)
    frozenset({MarketGroup.TENNIS_WINNER, MarketGroup.TENNIS_FIRST_SET}),
}


def are_compatible(leg_a: BetBuilderLeg, leg_b: BetBuilderLeg) -> tuple[bool, str]:
    """Check if two legs can coexist in a builder."""
    mg_pair = frozenset({leg_a.market_spec.market_group, leg_b.market_spec.market_group})
    if mg_pair in INCOMPATIBLE_PAIRS:
        return False, f"Markets {leg_a.market_spec.market_group.value} and {leg_b.market_spec.market_group.value} are incompatible"

    # Same market, same line, conflicting outcomes (e.g., over AND under on same line)
    if (leg_a.market_spec.market_group == leg_b.market_spec.market_group
            and leg_a.market_spec.line_value == leg_b.market_spec.line_value
            and leg_a.market_spec.side == leg_b.market_spec.side):
        if leg_a.outcome != leg_b.outcome:
            if {leg_a.outcome, leg_b.outcome} & {OutcomeType.OVER, OutcomeType.UNDER} == {OutcomeType.OVER, OutcomeType.UNDER}:
                return False, "Cannot combine Over and Under on the same line"
            if {leg_a.outcome, leg_b.outcome} & {OutcomeType.YES, OutcomeType.NO} == {OutcomeType.YES, OutcomeType.NO}:
                return False, "Cannot combine Yes and No on the same market"

    return True, ""


def check_all_compatible(legs: list[BetBuilderLeg]) -> tuple[bool, str]:
    """Check pairwise compatibility of all legs."""
    for i in range(len(legs)):
        for j in range(i + 1, len(legs)):
            ok, reason = are_compatible(legs[i], legs[j])
            if not ok:
                return False, reason
    return True, ""


# ────────────────────────────────────────────────────────────
# Correlation adjustment matrix
# ────────────────────────────────────────────────────────────

# Correlation penalty factors between category pairs
# Values < 1.0 reduce combined probability (positive correlation)
# Values > 1.0 increase combined probability (negative correlation)
CORRELATION_PENALTIES: dict[frozenset[CorrelationCategory], float] = {
    frozenset({CorrelationCategory.SAME_TEAM_ATTACK}): 0.88,
    frozenset({CorrelationCategory.SAME_TEAM_DEFENSE}): 0.90,
    frozenset({CorrelationCategory.GAME_PACE}): 0.85,
    frozenset({CorrelationCategory.GAME_TOTAL}): 0.87,
    frozenset({CorrelationCategory.PLAYER_USAGE}): 0.92,
    frozenset({CorrelationCategory.PLAYER_SCORING}): 0.90,
    frozenset({CorrelationCategory.SET_DYNAMICS}): 0.88,
    # Cross-category correlations
    frozenset({CorrelationCategory.SAME_TEAM_ATTACK, CorrelationCategory.GAME_TOTAL}): 0.82,
    frozenset({CorrelationCategory.SAME_TEAM_ATTACK, CorrelationCategory.GAME_PACE}): 0.84,
    frozenset({CorrelationCategory.SAME_TEAM_ATTACK, CorrelationCategory.PLAYER_SCORING}): 0.80,
    frozenset({CorrelationCategory.GAME_TOTAL, CorrelationCategory.GAME_PACE}): 0.83,
    frozenset({CorrelationCategory.PLAYER_USAGE, CorrelationCategory.PLAYER_SCORING}): 0.85,
    frozenset({CorrelationCategory.SAME_TEAM_DEFENSE, CorrelationCategory.GAME_TOTAL}): 0.86,
}

# Same category, same direction (both "over" type) extra penalty
SAME_DIRECTION_PENALTY = 0.92


def compute_correlation_adjustment(legs: list[BetBuilderLeg]) -> float:
    """Compute overall correlation adjustment factor for combined probability.

    Returns a factor < 1.0 for positively correlated legs (conservative),
    effectively reducing the combined probability.
    """
    if len(legs) <= 1:
        return 1.0

    total_adjustment = 1.0
    categories_seen: set[CorrelationCategory] = set()

    for i in range(len(legs)):
        for j in range(i + 1, len(legs)):
            leg_a, leg_b = legs[i], legs[j]

            # Check pairwise correlation categories
            cats_a = set(leg_a.correlation_categories)
            cats_b = set(leg_b.correlation_categories)

            # Same category overlap
            overlap = cats_a & cats_b
            for cat in overlap:
                key = frozenset({cat})
                penalty = CORRELATION_PENALTIES.get(key, 0.95)
                total_adjustment *= penalty
                categories_seen.add(cat)

            # Cross-category correlations
            for cat_a in cats_a:
                for cat_b in cats_b:
                    if cat_a != cat_b:
                        key = frozenset({cat_a, cat_b})
                        if key in CORRELATION_PENALTIES:
                            total_adjustment *= CORRELATION_PENALTIES[key]

            # Same direction penalty (both over/over or under/under on related markets)
            if (leg_a.outcome == leg_b.outcome
                    and leg_a.outcome in (OutcomeType.OVER, OutcomeType.YES)
                    and overlap):
                total_adjustment *= SAME_DIRECTION_PENALTY

    # Cap the total adjustment to avoid extremely low values
    return max(0.5, min(1.0, total_adjustment))


# ────────────────────────────────────────────────────────────
# Bet Builder service
# ────────────────────────────────────────────────────────────

class BetBuilderService:
    """Builds and validates bet builder combinations."""

    def __init__(self) -> None:
        self.registry = get_registry()

    def build_proposal(
        self, predictions: list[PredictionResult], legs_specs: list[MarketSpec],
    ) -> BetBuilderProposal:
        """Build a bet builder proposal from selected predictions."""
        pred_map: dict[str, PredictionResult] = {}
        for p in predictions:
            pred_map[p.market_spec.normalized_key + ":" + p.outcome_label] = p

        legs: list[BetBuilderLeg] = []
        for spec in legs_specs:
            # Find matching prediction
            for key, pred in pred_map.items():
                if pred.market_spec.normalized_key == spec.normalized_key:
                    defn = self.registry.get(spec.market_group)
                    corr_cats = defn.correlation_categories if defn else []
                    legs.append(BetBuilderLeg(
                        market_spec=spec,
                        outcome=pred.outcome,
                        outcome_label=pred.outcome_label,
                        individual_prob=pred.probability,
                        individual_fair_odds=pred.fair_odds,
                        correlation_categories=corr_cats,
                    ))
                    break

        if not legs:
            return BetBuilderProposal(
                game_id="",
                legs=[],
                naive_combined_prob=0.0,
                correlation_adjustment=1.0,
                adjusted_prob=0.0,
                adjusted_fair_odds=999.0,
                compatible=False,
                incompatibility_reason="No matching predictions found",
            )

        # Check compatibility
        compatible, reason = check_all_compatible(legs)

        # Naive combined probability (multiply)
        naive_prob = 1.0
        for leg in legs:
            naive_prob *= leg.individual_prob

        # Correlation adjustment
        corr_adj = compute_correlation_adjustment(legs)
        adjusted_prob = max(0.001, min(0.999, naive_prob * corr_adj))
        adjusted_fair_odds = round(1.0 / adjusted_prob, 3) if adjusted_prob > 0 else 999.0

        game_id = ""
        for key, pred in pred_map.items():
            game_id = pred.game_id
            break

        risk = RiskLevel.HIGH
        if adjusted_prob > 0.3:
            risk = RiskLevel.MEDIUM
        if adjusted_prob > 0.5:
            risk = RiskLevel.LOW

        return BetBuilderProposal(
            game_id=game_id,
            legs=legs,
            naive_combined_prob=round(naive_prob, 6),
            correlation_adjustment=round(corr_adj, 4),
            adjusted_prob=round(adjusted_prob, 6),
            adjusted_fair_odds=adjusted_fair_odds,
            compatible=compatible,
            incompatibility_reason=reason if not compatible else None,
            risk_level=risk,
        )

    def suggest_builders(
        self, predictions: list[PredictionResult],
        game_id: str, max_legs: int = 4, min_edge: float = 3.0,
    ) -> list[BetBuilderProposal]:
        """Auto-generate suggested bet builder combos with edge."""
        # Filter to predictions with reasonable probability
        good_preds = [p for p in predictions if 0.4 <= p.probability <= 0.8]
        if len(good_preds) < 2:
            good_preds = [p for p in predictions if 0.3 <= p.probability <= 0.85]

        # Group by market type for diversity
        by_type: dict[str, list[PredictionResult]] = {}
        for p in good_preds:
            mt = p.market_spec.market_type.value
            by_type.setdefault(mt, []).append(p)

        proposals: list[BetBuilderProposal] = []

        # Strategy 1: Pick one from each available category (2-3 legs)
        if len(by_type) >= 2:
            for num_legs in (2, 3, min(4, len(by_type))):
                types = list(by_type.keys())[:num_legs]
                selected_preds = [by_type[t][0] for t in types if by_type[t]]
                if len(selected_preds) >= 2:
                    legs_specs = [p.market_spec for p in selected_preds]
                    proposal = self.build_proposal(predictions, legs_specs)
                    if proposal.compatible:
                        proposals.append(proposal)

        # Strategy 2: High-prob combo (all > 60%)
        high_prob = sorted(
            [p for p in good_preds if p.probability > 0.6],
            key=lambda x: x.probability, reverse=True,
        )
        if len(high_prob) >= 2:
            selected = high_prob[:3]
            legs_specs = [p.market_spec for p in selected]
            proposal = self.build_proposal(predictions, legs_specs)
            if proposal.compatible:
                proposals.append(proposal)

        return proposals[:5]  # Max 5 suggestions
