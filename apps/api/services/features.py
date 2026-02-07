"""Feature engineering for all sports."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from packages.shared.enums.sport import Sport


@dataclass
class TeamFeatures:
    """Computed features for a team in a specific matchup."""
    team_id: str
    sport: Sport
    is_home: bool = False

    # Universal
    form_last5_win_pct: float = 0.5
    form_last10_win_pct: float = 0.5
    home_away_win_pct: float = 0.5

    # Soccer
    goals_scored_avg: float = 0.0
    goals_conceded_avg: float = 0.0
    xg_for_avg: float = 0.0
    xg_against_avg: float = 0.0
    shots_avg: float = 0.0
    sot_avg: float = 0.0
    corners_for_avg: float = 0.0
    corners_against_avg: float = 0.0
    cards_for_avg: float = 0.0
    cards_against_avg: float = 0.0
    fouls_avg: float = 0.0
    offsides_avg: float = 0.0
    clean_sheet_pct: float = 0.0
    btts_pct: float = 0.0
    attack_rating: float = 1.0
    defense_rating: float = 1.0

    # NBA
    pace: float = 100.0
    ortg: float = 110.0
    drtg: float = 110.0
    efg_pct: float = 0.5
    tov_pct: float = 0.13
    reb_pct: float = 0.5
    ft_rate: float = 0.25
    three_pct: float = 0.35
    rest_days: int = 1
    is_b2b: bool = False

    # NHL
    shots_for_avg_nhl: float = 30.0
    shots_against_avg_nhl: float = 30.0
    pp_pct: float = 0.2
    pk_pct: float = 0.8
    goalie_save_pct: float = 0.91

    # Tennis (team = player in tennis context)
    elo_overall: float = 1500.0
    elo_surface: float = 1500.0
    hold_pct: float = 0.8
    break_pct: float = 0.25
    aces_per_match: float = 5.0
    df_per_match: float = 2.0

    extra: dict = field(default_factory=dict)


@dataclass
class PlayerFeatures:
    """Computed features for a player."""
    player_id: str
    team_id: str
    sport: Sport

    minutes_avg: float = 0.0
    started_pct: float = 0.0

    # NBA
    points_avg: float = 0.0
    rebounds_avg: float = 0.0
    assists_avg: float = 0.0
    threes_avg: float = 0.0
    steals_avg: float = 0.0
    blocks_avg: float = 0.0
    turnovers_avg: float = 0.0
    usage_pct: float = 0.2
    pra_avg: float = 0.0

    # NHL
    goals_avg: float = 0.0
    nhl_assists_avg: float = 0.0
    nhl_points_avg: float = 0.0
    sog_avg: float = 0.0
    pp_points_avg: float = 0.0
    saves_avg: float = 0.0  # for goalies

    # Soccer
    soccer_goals_avg: float = 0.0
    soccer_assists_avg: float = 0.0
    soccer_shots_avg: float = 0.0
    soccer_sot_avg: float = 0.0
    soccer_cards_avg: float = 0.0
    soccer_fouls_avg: float = 0.0

    extra: dict = field(default_factory=dict)


def compute_team_features(
    team_id: str, sport: Sport, is_home: bool,
    game_stats: list[dict], season_stats: dict | None = None,
) -> TeamFeatures:
    """Build team features from raw stats."""
    feats = TeamFeatures(team_id=team_id, sport=sport, is_home=is_home)
    n = len(game_stats)
    if n == 0:
        return feats

    # Form calculations
    wins_5 = sum(1 for g in game_stats[:5] if g.get("result") == "W")
    wins_10 = sum(1 for g in game_stats[:10] if g.get("result") == "W")
    feats.form_last5_win_pct = wins_5 / min(5, n)
    feats.form_last10_win_pct = wins_10 / min(10, n)

    ha_games = [g for g in game_stats if g.get("is_home") == is_home]
    if ha_games:
        feats.home_away_win_pct = sum(1 for g in ha_games if g.get("result") == "W") / len(ha_games)

    def _avg(key: str, data: list[dict] | None = None) -> float:
        src = data or game_stats
        vals = [g.get(key, 0) for g in src if key in g]
        return sum(vals) / len(vals) if vals else 0.0

    if sport == Sport.SOCCER:
        feats.goals_scored_avg = _avg("goals_for")
        feats.goals_conceded_avg = _avg("goals_against")
        feats.xg_for_avg = _avg("xg_for")
        feats.xg_against_avg = _avg("xg_against")
        feats.shots_avg = _avg("shots")
        feats.sot_avg = _avg("sot")
        feats.corners_for_avg = _avg("corners_for")
        feats.corners_against_avg = _avg("corners_against")
        feats.cards_for_avg = _avg("yellows") + 2 * _avg("reds")
        feats.cards_against_avg = _avg("opp_yellows") + 2 * _avg("opp_reds")
        feats.fouls_avg = _avg("fouls")
        feats.offsides_avg = _avg("offsides")
        cs = sum(1 for g in game_stats if g.get("goals_against", 1) == 0)
        feats.clean_sheet_pct = cs / n
        btts = sum(1 for g in game_stats if g.get("goals_for", 0) > 0 and g.get("goals_against", 0) > 0)
        feats.btts_pct = btts / n
        league_avg_goals = season_stats.get("league_avg_goals", 1.35) if season_stats else 1.35
        feats.attack_rating = feats.goals_scored_avg / league_avg_goals if league_avg_goals > 0 else 1.0
        feats.defense_rating = feats.goals_conceded_avg / league_avg_goals if league_avg_goals > 0 else 1.0

    elif sport == Sport.NBA:
        feats.pace = _avg("pace") or 100.0
        feats.ortg = _avg("ortg") or 110.0
        feats.drtg = _avg("drtg") or 110.0
        feats.efg_pct = _avg("efg_pct") or 0.5
        feats.tov_pct = _avg("tov_pct") or 0.13
        feats.reb_pct = _avg("reb_pct") or 0.5
        feats.ft_rate = _avg("ft_rate") or 0.25
        feats.three_pct = _avg("three_pct") or 0.35
        if game_stats:
            latest = game_stats[0]
            feats.rest_days = latest.get("rest_days", 1)
            feats.is_b2b = feats.rest_days == 0

    elif sport == Sport.NHL:
        feats.shots_for_avg_nhl = _avg("shots_for") or 30.0
        feats.shots_against_avg_nhl = _avg("shots_against") or 30.0
        feats.pp_pct = _avg("pp_pct") or 0.2
        feats.pk_pct = _avg("pk_pct") or 0.8
        feats.goalie_save_pct = _avg("goalie_save_pct") or 0.91

    elif sport == Sport.TENNIS:
        feats.elo_overall = season_stats.get("elo_overall", 1500.0) if season_stats else 1500.0
        feats.elo_surface = season_stats.get("elo_surface", 1500.0) if season_stats else 1500.0
        feats.hold_pct = _avg("hold_pct") or 0.8
        feats.break_pct = _avg("break_pct") or 0.25
        feats.aces_per_match = _avg("aces") or 5.0
        feats.df_per_match = _avg("double_faults") or 2.0

    return feats


def compute_player_features(
    player_id: str, team_id: str, sport: Sport,
    game_stats: list[dict],
) -> PlayerFeatures:
    """Build player features from raw stats."""
    feats = PlayerFeatures(player_id=player_id, team_id=team_id, sport=sport)
    n = len(game_stats)
    if n == 0:
        return feats

    def _avg(key: str) -> float:
        vals = [g.get(key, 0) for g in game_stats if key in g]
        return sum(vals) / len(vals) if vals else 0.0

    feats.minutes_avg = _avg("minutes")
    feats.started_pct = sum(1 for g in game_stats if g.get("started")) / n

    if sport == Sport.NBA:
        feats.points_avg = _avg("points")
        feats.rebounds_avg = _avg("rebounds")
        feats.assists_avg = _avg("assists")
        feats.threes_avg = _avg("threes")
        feats.steals_avg = _avg("steals")
        feats.blocks_avg = _avg("blocks")
        feats.turnovers_avg = _avg("turnovers")
        feats.usage_pct = _avg("usage_pct") or 0.2
        feats.pra_avg = feats.points_avg + feats.rebounds_avg + feats.assists_avg

    elif sport == Sport.NHL:
        feats.goals_avg = _avg("goals")
        feats.nhl_assists_avg = _avg("assists")
        feats.nhl_points_avg = _avg("points")
        feats.sog_avg = _avg("sog")
        feats.pp_points_avg = _avg("pp_points")
        feats.saves_avg = _avg("saves")

    elif sport == Sport.SOCCER:
        feats.soccer_goals_avg = _avg("goals")
        feats.soccer_assists_avg = _avg("assists")
        feats.soccer_shots_avg = _avg("shots")
        feats.soccer_sot_avg = _avg("sot")
        feats.soccer_cards_avg = _avg("yellows")
        feats.soccer_fouls_avg = _avg("fouls")

    return feats
