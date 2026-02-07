"""Tests for segment profiles computation."""
import pytest

from apps.api.services.segment_profiles import (
    compute_team_segment_profiles,
    compute_matchup_segment_profiles,
    generate_segment_signals,
)


class TestTeamSegmentProfiles:
    """Test per-period team profile computation."""

    def test_full_time_profile(self):
        stats = [
            {"goals": 2, "goals_conceded": 1, "1h_goals": 1, "1h_goals_conceded": 0,
             "2h_goals": 1, "2h_goals_conceded": 1},
            {"goals": 1, "goals_conceded": 0, "1h_goals": 0, "1h_goals_conceded": 0,
             "2h_goals": 1, "2h_goals_conceded": 0},
            {"goals": 3, "goals_conceded": 2, "1h_goals": 2, "1h_goals_conceded": 1,
             "2h_goals": 1, "2h_goals_conceded": 1},
        ]
        profiles = compute_team_segment_profiles("team_a", stats)
        ft_profiles = [p for p in profiles if p.segment_period == "ft"]
        assert len(ft_profiles) == 1
        ft = ft_profiles[0]
        assert ft.offensive_rating == pytest.approx(2.0, abs=0.01)
        assert ft.defensive_rating == pytest.approx(1.0, abs=0.01)
        assert ft.net_rating == pytest.approx(1.0, abs=0.01)
        assert ft.sample_size == 3

    def test_half_profiles_generated(self):
        stats = [
            {"goals": 2, "goals_conceded": 1, "1h_goals": 1, "1h_goals_conceded": 0,
             "2h_goals": 1, "2h_goals_conceded": 1},
        ]
        profiles = compute_team_segment_profiles("team_a", stats)
        periods = {p.segment_period for p in profiles}
        assert "ft" in periods
        assert "1h" in periods
        assert "2h" in periods

    def test_empty_stats(self):
        profiles = compute_team_segment_profiles("team_a", [])
        assert profiles == []


class TestMatchupProfiles:
    """Test matchup profile computation."""

    def test_edge_calculation(self):
        stats_a = [
            {"goals": 2, "goals_conceded": 0, "1h_goals": 1, "1h_goals_conceded": 0,
             "2h_goals": 1, "2h_goals_conceded": 0},
        ]
        stats_b = [
            {"goals": 0, "goals_conceded": 2, "1h_goals": 0, "1h_goals_conceded": 1,
             "2h_goals": 0, "2h_goals_conceded": 1},
        ]
        profiles_a = compute_team_segment_profiles("a", stats_a)
        profiles_b = compute_team_segment_profiles("b", stats_b)
        matchups = compute_matchup_segment_profiles("a", "b", profiles_a, profiles_b)
        assert len(matchups) >= 1
        ft_matchup = [m for m in matchups if m.segment_period == "ft"]
        assert len(ft_matchup) == 1
        assert ft_matchup[0].adjusted_edge_pp > 0  # team a is better


class TestSegmentSignals:
    """Test signal generation from profiles."""

    def test_dominance_signal_generated(self):
        stats_a = [
            {"goals": 3, "goals_conceded": 0, "1h_goals": 2, "1h_goals_conceded": 0,
             "2h_goals": 1, "2h_goals_conceded": 0},
        ] * 5  # repeat for sample size
        stats_b = [
            {"goals": 0, "goals_conceded": 3, "1h_goals": 0, "1h_goals_conceded": 2,
             "2h_goals": 0, "2h_goals_conceded": 1},
        ] * 5
        profiles_a = compute_team_segment_profiles("a", stats_a)
        profiles_b = compute_team_segment_profiles("b", stats_b)
        matchups = compute_matchup_segment_profiles("a", "b", profiles_a, profiles_b)
        signals = generate_segment_signals("a", "b", "game1", matchups, profiles_a, profiles_b)
        dominance = [s for s in signals if s.signal_type.value == "segment_dominance"]
        assert len(dominance) >= 1
