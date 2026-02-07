'use client';

import { cn, sportIcon, sportLabel } from '@/lib/utils';
import type { FilterState, Sport } from '@/types';

const SPORTS: Sport[] = ['soccer', 'nba', 'nhl', 'tennis'];

const MARKET_GROUPS: Record<string, { label: string; sport?: string }[]> = {
  '': [{ label: 'All Markets' }],
  soccer: [
    { label: '1X2 Result', sport: 'soccer_1x2_ft' },
    { label: 'Totals (Goals)', sport: 'totals' },
    { label: 'BTTS', sport: 'soccer_btts' },
    { label: 'Corners Total', sport: 'soccer_corners_total' },
    { label: 'Corners Team', sport: 'soccer_corners_team' },
    { label: 'Cards Total', sport: 'soccer_cards_total' },
    { label: 'SOT Total', sport: 'soccer_sot_total' },
    { label: 'Shots Total', sport: 'soccer_shots_total' },
    { label: 'Correct Score', sport: 'soccer_correct_score' },
    { label: 'Clean Sheet', sport: 'soccer_clean_sheet' },
    { label: 'Player SOT', sport: 'soccer_sot_player' },
    { label: 'Anytime Scorer', sport: 'soccer_anytime_scorer' },
  ],
  nba: [
    { label: 'Moneyline', sport: 'nba_moneyline' },
    { label: 'Spread', sport: 'nba_spread' },
    { label: 'Totals', sport: 'nba_totals' },
    { label: 'Team Totals', sport: 'nba_team_totals' },
    { label: 'Player Points', sport: 'nba_player_points' },
    { label: 'Player Rebounds', sport: 'nba_player_rebounds' },
    { label: 'Player Assists', sport: 'nba_player_assists' },
    { label: 'Player Threes', sport: 'nba_player_threes' },
    { label: 'Player PRA', sport: 'nba_player_pra' },
  ],
  nhl: [
    { label: 'Moneyline', sport: 'nhl_moneyline' },
    { label: 'Puck Line', sport: 'nhl_puck_line' },
    { label: 'Totals', sport: 'nhl_totals' },
    { label: 'Team Totals', sport: 'nhl_team_totals' },
    { label: 'Reg Time 3-Way', sport: 'nhl_reg_time' },
    { label: 'Player SOG', sport: 'nhl_player_sog' },
    { label: 'Goalie Saves', sport: 'nhl_goalie_saves' },
  ],
  tennis: [
    { label: 'Match Winner', sport: 'tennis_winner' },
    { label: 'Set Betting', sport: 'tennis_set_betting' },
    { label: 'Total Games', sport: 'tennis_total_games' },
    { label: 'Set Totals', sport: 'tennis_set_totals' },
    { label: 'Tiebreak', sport: 'tennis_tiebreak' },
  ],
};

interface Props {
  filters: FilterState;
  onChange: (f: FilterState) => void;
}

export function FilterBlock({ filters, onChange }: Props) {
  const sportMarkets = MARKET_GROUPS[filters.sport] || [];

  return (
    <div className="card p-4 space-y-4">
      <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Filters</h3>

      {/* Date */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Date</label>
        <input
          type="date"
          value={filters.date}
          onChange={(e) => onChange({ ...filters, date: e.target.value })}
          className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-brand-500 focus:border-brand-500"
        />
      </div>

      {/* Sport */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Sport</label>
        <div className="grid grid-cols-2 gap-1.5">
          <button
            onClick={() => onChange({ ...filters, sport: '', marketGroup: '' })}
            className={cn(
              'px-2 py-1.5 text-xs font-medium rounded-md border transition-colors',
              filters.sport === '' ? 'bg-brand-600 text-white border-brand-600' : 'border-gray-300 hover:bg-gray-50',
            )}
          >
            All
          </button>
          {SPORTS.map((s) => (
            <button
              key={s}
              onClick={() => onChange({ ...filters, sport: s, marketGroup: '' })}
              className={cn(
                'px-2 py-1.5 text-xs font-medium rounded-md border transition-colors',
                filters.sport === s ? 'bg-brand-600 text-white border-brand-600' : 'border-gray-300 hover:bg-gray-50',
              )}
            >
              {sportIcon(s)} {sportLabel(s)}
            </button>
          ))}
        </div>
      </div>

      {/* Market Group */}
      {filters.sport && sportMarkets.length > 0 && (
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Market</label>
          <select
            value={filters.marketGroup}
            onChange={(e) => onChange({ ...filters, marketGroup: e.target.value })}
            className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md"
          >
            <option value="">All Markets</option>
            {sportMarkets.map((m) => (
              <option key={m.sport} value={m.sport}>
                {m.label}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Min Edge */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">
          Min Edge: {filters.minEdge}%
        </label>
        <input
          type="range"
          min={0}
          max={20}
          step={0.5}
          value={filters.minEdge}
          onChange={(e) => onChange({ ...filters, minEdge: Number(e.target.value) })}
          className="w-full accent-brand-600"
        />
      </div>

      {/* Min Probability */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">
          Min Prob: {(filters.minProb * 100).toFixed(0)}%
        </label>
        <input
          type="range"
          min={0}
          max={0.9}
          step={0.05}
          value={filters.minProb}
          onChange={(e) => onChange({ ...filters, minProb: Number(e.target.value) })}
          className="w-full accent-brand-600"
        />
      </div>

      {/* Hide no odds */}
      <label className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer">
        <input
          type="checkbox"
          checked={filters.hideNoOdds}
          onChange={(e) => onChange({ ...filters, hideNoOdds: e.target.checked })}
          className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
        />
        Hide bets without odds
      </label>
    </div>
  );
}
