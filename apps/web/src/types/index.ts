export interface TeamInfo {
  team_id: string;
  name: string;
  short_name: string;
  logo_url?: string;
}

export interface GameInfo {
  game_id: string;
  sport: Sport;
  league: string;
  season: string;
  home_team: TeamInfo;
  away_team: TeamInfo;
  start_time: string;
  venue: string;
  is_playoff: boolean;
  status: string;
}

export type Sport = 'soccer' | 'nba' | 'nhl' | 'tennis';

export type BetTag = 'value' | 'high_conf' | 'longshot';
export type RiskLevel = 'low' | 'medium' | 'high';

export interface ExplanationFactor {
  name: string;
  value: number;
  description: string;
  importance?: number;
}

export interface MarketSpec {
  market_group: string;
  market_type: string;
  period: string;
  side: string;
  line_value: number | null;
  line_unit: string | null;
  player_id: string | null;
  bucket_label: string | null;
}

export interface BestBet {
  game_id: string;
  sport: Sport;
  league: string;
  home_team: string;
  away_team: string;
  start_time: string;
  market_name: string;
  market_spec: MarketSpec;
  outcome: string;
  outcome_label: string;
  bookmaker_odds: number;
  implied_prob: number;
  model_prob: number;
  fair_odds: number;
  edge_pct: number;
  interval_low: number;
  interval_high: number;
  factors: ExplanationFactor[];
  risk_note: string;
  risk_level: RiskLevel;
  tag: BetTag;
}

export interface PredictionResult {
  game_id: string;
  market: string;
  market_group: string;
  outcome: string;
  outcome_label: string;
  probability: number;
  fair_odds: number;
  interval: [number, number];
  factors: ExplanationFactor[];
  model_version: string;
}

export interface OddsSnapshot {
  game_id: string;
  bookmaker: string;
  market_key: string;
  outcome_label: string;
  line: number | null;
  price: number;
  implied_prob: number | null;
  timestamp: string;
}

export interface BacktestMetrics {
  total_bets: number;
  wins: number;
  losses: number;
  win_rate: number;
  roi_pct: number;
  log_loss: number | null;
  brier_score: number | null;
  calibration_error: number | null;
  max_drawdown: number;
  avg_edge: number;
}

export interface BacktestReport {
  sport: string;
  league: string;
  market_group: string;
  period_start: string;
  period_end: string;
  model_version: string;
  flat_stake: BacktestMetrics;
  kelly_stake: BacktestMetrics | null;
  sample_size: number;
  notes: string;
}

export interface MarketDefinition {
  market_group: string;
  market_type: string;
  sport: string;
  display_name: string;
  description: string;
  supported_periods: string[];
  supported_sides: string[];
  line_unit: string | null;
  default_lines: number[];
  outcomes: { type: string; label: string }[];
  requires_player: boolean;
  model_family: string;
}

export interface BetBuilderLeg {
  market_spec: MarketSpec;
  outcome: string;
  outcome_label: string;
  individual_prob: number;
  individual_fair_odds: number;
}

export interface BetBuilderProposal {
  game_id: string;
  legs: BetBuilderLeg[];
  naive_combined_prob: number;
  correlation_adjustment: number;
  adjusted_prob: number;
  adjusted_fair_odds: number;
  bookmaker_combo_odds: number | null;
  edge_pct: number | null;
  risk_level: RiskLevel;
  compatible: boolean;
  incompatibility_reason: string | null;
}

export interface FilterState {
  date: string;
  sport: Sport | '';
  league: string;
  marketGroup: string;
  minEdge: number;
  minProb: number;
  minConf: number;
  hideNoOdds: boolean;
}

// ────────────────────────────────────────────────────────────
// Intelligence Signals & Alerts (upgrade)
// ────────────────────────────────────────────────────────────

export type SignalType =
  | 'odds_move'
  | 'lineup_confirmed'
  | 'key_player_out'
  | 'matchup_trend'
  | 'segment_dominance'
  | 'fatigue_edge'
  | 'rest_advantage'
  | 'schedule_pressure'
  | 'playoff_context'
  | 'season_trend';

export interface IntelligenceSignal {
  id: string;
  sport_id: string | null;
  league_id: string | null;
  game_id: string | null;
  team_id: string | null;
  player_id: string | null;
  signal_type: SignalType;
  signal_strength: number;
  reliability: number;
  headline: string;
  description: string;
  affected_market_groups: string[];
  affected_periods: string[];
  metadata: Record<string, any>;
  created_at: string;
}

export interface OddsMove {
  game_id: string;
  bookmaker: string;
  market_key: string;
  outcome_label: string;
  old_price: number;
  new_price: number;
  old_implied_prob: number;
  new_implied_prob: number;
  delta_implied_prob: number;
  old_line: number | null;
  new_line: number | null;
  detected_at: string;
}

export interface AdjustedPrediction {
  id: number;
  base_prediction_id: number;
  game_id: string;
  market_key: string;
  outcome_label: string;
  base_prob: number;
  adjusted_prob: number;
  adjusted_fair_odds: number;
  adjusted_edge: number | null;
  interval_low: number;
  interval_high: number;
  applied_signal_ids: string[];
  signal_reasons: { signal_id: string; signal_type: string; headline: string; delta: number; reason: string }[];
  created_at: string;
}

export interface NotificationRule {
  id: number;
  user_key: string;
  sports: string[];
  leagues: string[];
  market_groups: string[];
  min_edge: number;
  min_confidence: number;
  min_prob: number;
  quiet_hours: Record<string, string>;
  max_alerts_per_game: number;
  max_alerts_per_day: number;
  cooldown_minutes: number;
  enabled: boolean;
  created_at: string | null;
}

export interface NotificationSent {
  id: number;
  rule_id: number;
  game_id: string;
  market_key: string;
  line: number | null;
  selection: string;
  edge_pct: number;
  model_prob: number;
  fair_odds: number;
  signals_summary: { signal_id: string; type: string; headline: string; strength: number }[];
  payload: Record<string, any>;
  sent_at: string;
  dedup_hash: string;
}
