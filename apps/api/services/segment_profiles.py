"""Segment Profiles — compute per-period team and matchup profiles, emit signals."""
from __future__ import annotations

import uuid
from datetime import datetime

from packages.shared.enums.market import SignalType
from packages.shared.schemas.signals import (
    IntelligenceSignalOut,
    MatchupSegmentProfileOut,
    TeamSegmentProfileOut,
)


def compute_team_segment_profiles(
    team_id: str,
    game_stats: list[dict],
) -> list[TeamSegmentProfileOut]:
    """Compute per-period performance profiles for a team.

    game_stats: list of dicts from TeamGameStats.stats JSONB
    Each dict has period-level data, e.g. {"1h_goals": 1, "2h_goals": 0, "goals": 1, ...}

    Returns TeamSegmentProfileOut for each segment (1h, 2h, ft, ot).
    """
    if not game_stats:
        return []

    profiles = []
    now = datetime.utcnow()

    # Full time profile
    off_vals = [g.get("goals", g.get("points", 0)) or 0 for g in game_stats]
    def_vals = [g.get("goals_conceded", g.get("points_against", 0)) or 0 for g in game_stats]
    n = len(game_stats)
    if n == 0:
        return []

    off_avg = sum(off_vals) / n
    def_avg = sum(def_vals) / n
    net = off_avg - def_avg

    # Volatility: std dev of scoring
    off_var = sum((v - off_avg) ** 2 for v in off_vals) / max(n - 1, 1)
    volatility = off_var ** 0.5

    # Clutch factor: performance in recent 3 vs overall
    recent = off_vals[-3:] if len(off_vals) >= 3 else off_vals
    clutch = (sum(recent) / len(recent)) - off_avg if recent else 0.0

    profiles.append(TeamSegmentProfileOut(
        id=0,
        team_id=team_id,
        segment_period="ft",
        offensive_rating=round(off_avg, 3),
        defensive_rating=round(def_avg, 3),
        net_rating=round(net, 3),
        volatility=round(volatility, 3),
        clutch_factor=round(clutch, 3),
        sample_size=n,
        updated_at=now,
    ))

    # First half profile
    h1_off = [g.get("1h_goals", g.get("1h_points", 0)) or 0 for g in game_stats]
    h1_def = [g.get("1h_goals_conceded", g.get("1h_points_against", 0)) or 0 for g in game_stats]
    if any(v > 0 for v in h1_off) or any(v > 0 for v in h1_def):
        h1_off_avg = sum(h1_off) / n
        h1_def_avg = sum(h1_def) / n
        h1_var = sum((v - h1_off_avg) ** 2 for v in h1_off) / max(n - 1, 1)
        profiles.append(TeamSegmentProfileOut(
            id=0,
            team_id=team_id,
            segment_period="1h",
            offensive_rating=round(h1_off_avg, 3),
            defensive_rating=round(h1_def_avg, 3),
            net_rating=round(h1_off_avg - h1_def_avg, 3),
            volatility=round(h1_var ** 0.5, 3),
            clutch_factor=0.0,
            sample_size=n,
            updated_at=now,
        ))

    # Second half profile
    h2_off = [g.get("2h_goals", g.get("2h_points", 0)) or 0 for g in game_stats]
    h2_def = [g.get("2h_goals_conceded", g.get("2h_points_against", 0)) or 0 for g in game_stats]
    if any(v > 0 for v in h2_off) or any(v > 0 for v in h2_def):
        h2_off_avg = sum(h2_off) / n
        h2_def_avg = sum(h2_def) / n
        h2_var = sum((v - h2_off_avg) ** 2 for v in h2_off) / max(n - 1, 1)
        profiles.append(TeamSegmentProfileOut(
            id=0,
            team_id=team_id,
            segment_period="2h",
            offensive_rating=round(h2_off_avg, 3),
            defensive_rating=round(h2_def_avg, 3),
            net_rating=round(h2_off_avg - h2_def_avg, 3),
            volatility=round(h2_var ** 0.5, 3),
            clutch_factor=0.0,
            sample_size=n,
            updated_at=now,
        ))

    return profiles


def compute_matchup_segment_profiles(
    team_a_id: str,
    team_b_id: str,
    team_a_profiles: list[TeamSegmentProfileOut],
    team_b_profiles: list[TeamSegmentProfileOut],
    h2h_stats: list[dict] | None = None,
) -> list[MatchupSegmentProfileOut]:
    """Compute head-to-head segment analysis between two teams.

    Compares segment profiles and optionally uses H2H data.
    Returns MatchupSegmentProfileOut for each common segment period.
    """
    now = datetime.utcnow()
    profiles_a = {p.segment_period: p for p in team_a_profiles}
    profiles_b = {p.segment_period: p for p in team_b_profiles}

    common_periods = set(profiles_a.keys()) & set(profiles_b.keys())
    results = []

    for period in sorted(common_periods):
        a = profiles_a[period]
        b = profiles_b[period]

        # Edge: (A_off - B_def) - (B_off - A_def), in points/goals per game
        edge_pp = (a.offensive_rating - b.defensive_rating) - (b.offensive_rating - a.defensive_rating)

        # H2H effect
        h2h_effect = 0.0
        h2h_sample = 0
        if h2h_stats:
            h2h_sample = len(h2h_stats)
            a_wins = sum(1 for g in h2h_stats if g.get("winner") == team_a_id)
            b_wins = sum(1 for g in h2h_stats if g.get("winner") == team_b_id)
            if h2h_sample > 0:
                h2h_effect = (a_wins - b_wins) / h2h_sample * 2.0  # scale to pp

        # Confidence: based on sample sizes
        min_sample = min(a.sample_size, b.sample_size)
        confidence = min(1.0, min_sample / 20.0)

        # Style tags
        style_tags = []
        if a.volatility > 1.0 or b.volatility > 1.0:
            style_tags.append("high_variance")
        if abs(edge_pp) > 0.5:
            style_tags.append("clear_edge")
        if a.clutch_factor > 0.3:
            style_tags.append("a_clutch")
        if b.clutch_factor > 0.3:
            style_tags.append("b_clutch")

        results.append(MatchupSegmentProfileOut(
            id=0,
            team_a_id=team_a_id,
            team_b_id=team_b_id,
            segment_period=period,
            adjusted_edge_pp=round(edge_pp, 3),
            h2h_weighted_effect_pp=round(h2h_effect, 3),
            confidence=round(confidence, 3),
            style_tags=style_tags,
            sample_size=min_sample + h2h_sample,
            updated_at=now,
        ))

    return results


def generate_segment_signals(
    team_a_id: str,
    team_b_id: str,
    game_id: str,
    matchup_profiles: list[MatchupSegmentProfileOut],
    team_a_profiles: list[TeamSegmentProfileOut],
    team_b_profiles: list[TeamSegmentProfileOut],
) -> list[IntelligenceSignalOut]:
    """Generate SEGMENT_DOMINANCE and MATCHUP_TREND signals from profiles."""
    signals = []
    now = datetime.utcnow()

    for mp in matchup_profiles:
        # SEGMENT_DOMINANCE: team clearly better in a period
        if abs(mp.adjusted_edge_pp) > 0.3 and mp.confidence >= 0.4:
            dominant = team_a_id if mp.adjusted_edge_pp > 0 else team_b_id
            strength = min(1.0, abs(mp.adjusted_edge_pp) / 1.5)
            signals.append(IntelligenceSignalOut(
                id=str(uuid.uuid4()),
                game_id=game_id,
                team_id=dominant,
                signal_type=SignalType.SEGMENT_DOMINANCE,
                signal_strength=round(strength, 3),
                reliability=round(mp.confidence, 3),
                headline=f"{'Team A' if dominant == team_a_id else 'Team B'} dominates {mp.segment_period} segment ({mp.adjusted_edge_pp:+.2f}pp)",
                description=(
                    f"In the {mp.segment_period} segment, {dominant} has a "
                    f"{abs(mp.adjusted_edge_pp):.2f}pp advantage based on "
                    f"{mp.sample_size} samples. Confidence: {mp.confidence:.0%}."
                ),
                affected_market_groups=["totals", "team_totals", "moneyline", "spread"],
                affected_periods=[mp.segment_period],
                metadata={
                    "edge_pp": mp.adjusted_edge_pp,
                    "segment": mp.segment_period,
                    "dominant_team": dominant,
                    "confidence": mp.confidence,
                },
                created_at=now,
            ))

        # MATCHUP_TREND: H2H effect is notable
        if abs(mp.h2h_weighted_effect_pp) > 0.5:
            favored = team_a_id if mp.h2h_weighted_effect_pp > 0 else team_b_id
            strength = min(1.0, abs(mp.h2h_weighted_effect_pp) / 2.0)
            signals.append(IntelligenceSignalOut(
                id=str(uuid.uuid4()),
                game_id=game_id,
                team_id=favored,
                signal_type=SignalType.MATCHUP_TREND,
                signal_strength=round(strength, 3),
                reliability=min(0.7, mp.confidence),
                headline=f"H2H trend favors {'Team A' if favored == team_a_id else 'Team B'} in {mp.segment_period}",
                description=(
                    f"Head-to-head data shows a {abs(mp.h2h_weighted_effect_pp):.2f}pp "
                    f"weighted effect favoring {favored} in {mp.segment_period} period."
                ),
                affected_market_groups=["moneyline", "spread", "totals"],
                affected_periods=[mp.segment_period],
                metadata={
                    "h2h_effect_pp": mp.h2h_weighted_effect_pp,
                    "segment": mp.segment_period,
                    "favored_team": favored,
                },
                created_at=now,
            ))

    return signals
