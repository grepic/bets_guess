'use client';

import { useState } from 'react';
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
    { label: 'Cards Total', sport: 'soccer_cards_total' },
    { label: 'Correct Score', sport: 'soccer_correct_score' },
  ],
  nba: [
    { label: 'Moneyline', sport: 'nba_moneyline' },
    { label: 'Spread', sport: 'nba_spread' },
    { label: 'Totals', sport: 'nba_totals' },
    { label: 'Team Totals', sport: 'nba_team_totals' },
  ],
  nhl: [
    { label: 'Moneyline', sport: 'nhl_moneyline' },
    { label: 'Puck Line', sport: 'nhl_puck_line' },
    { label: 'Totals', sport: 'nhl_totals' },
  ],
  tennis: [
    { label: 'Match Winner', sport: 'tennis_winner' },
    { label: 'Total Games', sport: 'tennis_total_games' },
    { label: 'Set Betting', sport: 'tennis_set_betting' },
  ],
};

interface Props {
  filters: FilterState;
  onChange: (f: FilterState) => void;
}

export function FilterBlock({ filters, onChange }: Props) {
  const [collapsed, setCollapsed] = useState(true);
  const sportMarkets = MARKET_GROUPS[filters.sport] || [];

  const content = (
    <div className="space-y-4">
      {/* Date */}
      <div>
        <label className="stat-label mb-1.5 block">Date</label>
        <input
          type="date"
          value={filters.date}
          onChange={(e) => onChange({ ...filters, date: e.target.value })}
          className="input"
        />
      </div>

      {/* Sport */}
      <div>
        <label className="stat-label mb-1.5 block">Sport</label>
        <div className="grid grid-cols-3 lg:grid-cols-2 gap-1.5">
          <button
            onClick={() => onChange({ ...filters, sport: '', marketGroup: '' })}
            className={cn(
              'px-2 py-2 text-xs font-semibold rounded-lg border transition-all duration-150',
              filters.sport === ''
                ? 'bg-brand-600 text-white border-brand-600 shadow-sm'
                : 'border-gray-200 text-gray-600 hover:border-gray-300 hover:bg-gray-50',
            )}
          >
            All
          </button>
          {SPORTS.map((s) => (
            <button
              key={s}
              onClick={() => onChange({ ...filters, sport: s, marketGroup: '' })}
              className={cn(
                'px-2 py-2 text-xs font-semibold rounded-lg border transition-all duration-150',
                filters.sport === s
                  ? 'bg-brand-600 text-white border-brand-600 shadow-sm'
                  : 'border-gray-200 text-gray-600 hover:border-gray-300 hover:bg-gray-50',
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
          <label className="stat-label mb-1.5 block">Market</label>
          <select
            value={filters.marketGroup}
            onChange={(e) => onChange({ ...filters, marketGroup: e.target.value })}
            className="select"
          >
            <option value="">All Markets</option>
            {sportMarkets.map((m) => (
              <option key={m.sport} value={m.sport}>{m.label}</option>
            ))}
          </select>
        </div>
      )}

      {/* Min Edge */}
      <div>
        <label className="stat-label mb-1.5 flex items-center justify-between">
          <span>Min Edge</span>
          <span className="text-brand-600 font-bold">{filters.minEdge}%</span>
        </label>
        <input
          type="range"
          min={0}
          max={20}
          step={0.5}
          value={filters.minEdge}
          onChange={(e) => onChange({ ...filters, minEdge: Number(e.target.value) })}
          className="w-full accent-brand-600 h-1.5"
        />
      </div>

      {/* Min Probability */}
      <div>
        <label className="stat-label mb-1.5 flex items-center justify-between">
          <span>Min Probability</span>
          <span className="text-brand-600 font-bold">{(filters.minProb * 100).toFixed(0)}%</span>
        </label>
        <input
          type="range"
          min={0}
          max={0.9}
          step={0.05}
          value={filters.minProb}
          onChange={(e) => onChange({ ...filters, minProb: Number(e.target.value) })}
          className="w-full accent-brand-600 h-1.5"
        />
      </div>

      {/* Hide no odds */}
      <label className="flex items-center gap-2.5 text-xs text-gray-600 cursor-pointer group">
        <input
          type="checkbox"
          checked={filters.hideNoOdds}
          onChange={(e) => onChange({ ...filters, hideNoOdds: e.target.checked })}
          className="w-4 h-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500 transition"
        />
        <span className="group-hover:text-gray-900 transition-colors">Hide bets without odds</span>
      </label>
    </div>
  );

  return (
    <>
      {/* Desktop: always visible sidebar */}
      <div className="hidden lg:block">
        <div className="card p-4 sticky top-20">
          <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">Filters</h3>
          {content}
        </div>
      </div>

      {/* Mobile: collapsible */}
      <div className="lg:hidden">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full card p-3 flex items-center justify-between"
        >
          <span className="text-xs font-bold text-gray-500 uppercase tracking-widest">Filters</span>
          <svg
            className={cn('w-4 h-4 text-gray-400 transition-transform', !collapsed && 'rotate-180')}
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {!collapsed && (
          <div className="card p-4 mt-2 animate-slide-down">
            {content}
          </div>
        )}
      </div>
    </>
  );
}
