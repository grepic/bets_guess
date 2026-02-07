from enum import Enum


class MarketType(str, Enum):
    RESULT = "result"
    TOTALS = "totals"
    TEAM_TOTALS = "team_totals"
    HANDICAP = "handicap"
    PLAYER_PROP = "player_prop"
    TEAM_PROP = "team_prop"
    CORRECT_SCORE = "correct_score"
    BUILDER_COMBO = "builder_combo"
    RACE_TO = "race_to"
    WINNING_MARGIN = "winning_margin"
    ODD_EVEN = "odd_even"
    YES_NO = "yes_no"


class MarketGroup(str, Enum):
    # ── CORE (all sports) ──
    MONEYLINE = "moneyline"
    DRAW_NO_BET = "draw_no_bet"
    DOUBLE_CHANCE = "double_chance"
    SPREAD = "spread"
    TOTALS = "totals"
    TEAM_TOTALS = "team_totals"
    PERIOD_WINNER = "period_winner"
    PERIOD_TOTALS = "period_totals"
    ODD_EVEN = "odd_even"
    WINNING_MARGIN = "winning_margin"

    # ── SOCCER ──
    SOCCER_1X2_FT = "soccer_1x2_ft"
    SOCCER_1X2_HT = "soccer_1x2_ht"
    SOCCER_CORRECT_SCORE = "soccer_correct_score"
    SOCCER_BTTS = "soccer_btts"
    SOCCER_BTTS_OU = "soccer_btts_ou"
    SOCCER_TEAM_SCORE = "soccer_team_score"
    SOCCER_FIRST_TEAM_SCORE = "soccer_first_team_score"
    SOCCER_LAST_TEAM_SCORE = "soccer_last_team_score"
    SOCCER_FIRST_GOAL_TIME = "soccer_first_goal_time"
    SOCCER_CLEAN_SHEET = "soccer_clean_sheet"
    SOCCER_EXACT_GOALS = "soccer_exact_goals"
    SOCCER_WIN_TO_NIL = "soccer_win_to_nil"
    # Corners
    SOCCER_CORNERS_TOTAL = "soccer_corners_total"
    SOCCER_CORNERS_TEAM = "soccer_corners_team"
    SOCCER_CORNERS_HANDICAP = "soccer_corners_handicap"
    SOCCER_CORNERS_1H = "soccer_corners_1h"
    SOCCER_CORNERS_RACE = "soccer_corners_race"
    SOCCER_CORNERS_MOST = "soccer_corners_most"
    SOCCER_CORNERS_EXACT = "soccer_corners_exact"
    # Cards
    SOCCER_CARDS_TOTAL = "soccer_cards_total"
    SOCCER_CARDS_TEAM = "soccer_cards_team"
    SOCCER_CARDS_PLAYER = "soccer_cards_player"
    SOCCER_RED_CARD = "soccer_red_card"
    SOCCER_CARDS_HANDICAP = "soccer_cards_handicap"
    SOCCER_FOULS_TOTAL = "soccer_fouls_total"
    SOCCER_OFFSIDES_TOTAL = "soccer_offsides_total"
    # Shots
    SOCCER_SHOTS_TOTAL = "soccer_shots_total"
    SOCCER_SOT_TOTAL = "soccer_sot_total"
    SOCCER_SHOTS_TEAM = "soccer_shots_team"
    SOCCER_SOT_TEAM = "soccer_sot_team"
    SOCCER_SHOTS_PLAYER = "soccer_shots_player"
    SOCCER_SOT_PLAYER = "soccer_sot_player"
    SOCCER_PLAYER_SOT_THRESHOLD = "soccer_player_sot_threshold"
    # Player scoring
    SOCCER_ANYTIME_SCORER = "soccer_anytime_scorer"
    SOCCER_FIRST_SCORER = "soccer_first_scorer"
    SOCCER_PLAYER_ASSISTS = "soccer_player_assists"
    # Bet builder
    SOCCER_BET_BUILDER = "soccer_bet_builder"

    # ── NBA ──
    NBA_MONEYLINE = "nba_moneyline"
    NBA_SPREAD = "nba_spread"
    NBA_TOTALS = "nba_totals"
    NBA_TEAM_TOTALS = "nba_team_totals"
    NBA_1H_WINNER = "nba_1h_winner"
    NBA_2H_WINNER = "nba_2h_winner"
    NBA_QUARTER_WINNER = "nba_quarter_winner"
    NBA_1Q_TOTALS = "nba_1q_totals"
    NBA_1H_TOTALS = "nba_1h_totals"
    NBA_RACE_TO = "nba_race_to"
    NBA_WINNING_MARGIN = "nba_winning_margin"
    NBA_HIGHEST_SCORING = "nba_highest_scoring"
    # Player props
    NBA_PLAYER_POINTS = "nba_player_points"
    NBA_PLAYER_REBOUNDS = "nba_player_rebounds"
    NBA_PLAYER_ASSISTS = "nba_player_assists"
    NBA_PLAYER_THREES = "nba_player_threes"
    NBA_PLAYER_STEALS = "nba_player_steals"
    NBA_PLAYER_BLOCKS = "nba_player_blocks"
    NBA_PLAYER_TURNOVERS = "nba_player_turnovers"
    NBA_PLAYER_PRA = "nba_player_pra"
    NBA_PLAYER_PR = "nba_player_pr"
    NBA_PLAYER_PA = "nba_player_pa"
    NBA_PLAYER_RA = "nba_player_ra"
    NBA_PLAYER_DOUBLE_DOUBLE = "nba_player_double_double"
    NBA_PLAYER_TRIPLE_DOUBLE = "nba_player_triple_double"
    NBA_FIRST_BASKET = "nba_first_basket"
    NBA_PLAYER_MILESTONES = "nba_player_milestones"
    # Team props
    NBA_TEAM_THREES = "nba_team_threes"
    NBA_TEAM_REBOUNDS = "nba_team_rebounds"
    NBA_TEAM_ASSISTS = "nba_team_assists"

    # ── NHL ──
    NHL_MONEYLINE = "nhl_moneyline"
    NHL_PUCK_LINE = "nhl_puck_line"
    NHL_TOTALS = "nhl_totals"
    NHL_TEAM_TOTALS = "nhl_team_totals"
    NHL_PERIOD_WINNER = "nhl_period_winner"
    NHL_PERIOD_TOTALS = "nhl_period_totals"
    NHL_REG_TIME = "nhl_reg_time"
    NHL_WINNING_MARGIN = "nhl_winning_margin"
    # Player props
    NHL_PLAYER_GOALS = "nhl_player_goals"
    NHL_PLAYER_ASSISTS = "nhl_player_assists"
    NHL_PLAYER_POINTS = "nhl_player_points"
    NHL_PLAYER_SOG = "nhl_player_sog"
    NHL_PLAYER_PP_POINTS = "nhl_player_pp_points"
    NHL_GOALIE_SAVES = "nhl_goalie_saves"
    NHL_ANYTIME_SCORER = "nhl_anytime_scorer"
    # Team props
    NHL_TEAM_SOG = "nhl_team_sog"
    NHL_TEAM_PP_GOALS = "nhl_team_pp_goals"

    # ── TENNIS ──
    TENNIS_WINNER = "tennis_winner"
    TENNIS_SET_BETTING = "tennis_set_betting"
    TENNIS_TOTAL_GAMES = "tennis_total_games"
    TENNIS_GAMES_HANDICAP = "tennis_games_handicap"
    TENNIS_SET_TOTALS = "tennis_set_totals"
    TENNIS_FIRST_SET = "tennis_first_set"
    TENNIS_TIEBREAK = "tennis_tiebreak"
    TENNIS_PLAYER_ACES = "tennis_player_aces"
    TENNIS_PLAYER_DFS = "tennis_player_dfs"

    @classmethod
    def for_sport(cls, sport_value: str) -> list["MarketGroup"]:
        prefix_map = {
            "soccer": "soccer_",
            "nba": "nba_",
            "nhl": "nhl_",
            "tennis": "tennis_",
        }
        prefix = prefix_map.get(sport_value, "")
        core = [
            cls.MONEYLINE, cls.DRAW_NO_BET, cls.DOUBLE_CHANCE,
            cls.SPREAD, cls.TOTALS, cls.TEAM_TOTALS,
            cls.PERIOD_WINNER, cls.PERIOD_TOTALS,
            cls.ODD_EVEN, cls.WINNING_MARGIN,
        ]
        sport_specific = [m for m in cls if m.value.startswith(prefix)]
        return core + sport_specific


class OutcomeType(str, Enum):
    OVER = "over"
    UNDER = "under"
    HOME = "home"
    AWAY = "away"
    DRAW = "draw"
    YES = "yes"
    NO = "no"
    EXACT_SCORE = "exact_score"
    BUCKET = "bucket"
    PLAYER = "player"


class Period(str, Enum):
    FULL_TIME = "ft"
    FIRST_HALF = "1h"
    SECOND_HALF = "2h"
    FIRST_QUARTER = "1q"
    SECOND_QUARTER = "2q"
    THIRD_QUARTER = "3q"
    FOURTH_QUARTER = "4q"
    FIRST_PERIOD = "1p"
    SECOND_PERIOD = "2p"
    THIRD_PERIOD = "3p"
    SET_1 = "set1"
    SET_2 = "set2"
    SET_3 = "set3"
    SET_4 = "set4"
    SET_5 = "set5"
    MATCH = "match"
    REGULATION = "regulation"


class Side(str, Enum):
    HOME = "home"
    AWAY = "away"
    TOTAL = "total"
    PLAYER = "player"


class LineUnit(str, Enum):
    GOALS = "goals"
    POINTS = "points"
    CORNERS = "corners"
    CARDS = "cards"
    SHOTS = "shots"
    SHOTS_ON_TARGET = "shots_on_target"
    REBOUNDS = "rebounds"
    ASSISTS = "assists"
    THREES = "threes"
    STEALS = "steals"
    BLOCKS = "blocks"
    TURNOVERS = "turnovers"
    GAMES = "games"
    SETS = "sets"
    ACES = "aces"
    DOUBLE_FAULTS = "double_faults"
    SAVES = "saves"
    FOULS = "fouls"
    OFFSIDES = "offsides"
    MINUTES = "minutes"
    COMBO = "combo"


class CorrelationCategory(str, Enum):
    SAME_TEAM_ATTACK = "same_team_attack"
    SAME_TEAM_DEFENSE = "same_team_defense"
    GAME_PACE = "game_pace"
    GAME_TOTAL = "game_total"
    PLAYER_USAGE = "player_usage"
    PLAYER_SCORING = "player_scoring"
    SET_DYNAMICS = "set_dynamics"
    INDEPENDENT = "independent"


class BetTag(str, Enum):
    VALUE = "value"
    HIGH_CONF = "high_conf"
    LONGSHOT = "longshot"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SignalType(str, Enum):
    ODDS_MOVE = "odds_move"
    LINEUP_CONFIRMED = "lineup_confirmed"
    KEY_PLAYER_OUT = "key_player_out"
    MATCHUP_TREND = "matchup_trend"
    SEGMENT_DOMINANCE = "segment_dominance"
    FATIGUE_EDGE = "fatigue_edge"
    REST_ADVANTAGE = "rest_advantage"
    SCHEDULE_PRESSURE = "schedule_pressure"
    PLAYOFF_CONTEXT = "playoff_context"
    SEASON_TREND = "season_trend"
