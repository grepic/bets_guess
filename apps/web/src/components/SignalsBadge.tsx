'use client';

import type { IntelligenceSignal } from '@/types';
import { cn } from '@/lib/utils';

interface Props {
  signals: IntelligenceSignal[];
  compact?: boolean;
}

const SIGNAL_COLORS: Record<string, string> = {
  odds_move: 'bg-blue-100 text-blue-800 border-blue-200',
  lineup_confirmed: 'bg-green-100 text-green-800 border-green-200',
  key_player_out: 'bg-red-100 text-red-800 border-red-200',
  matchup_trend: 'bg-purple-100 text-purple-800 border-purple-200',
  segment_dominance: 'bg-indigo-100 text-indigo-800 border-indigo-200',
  fatigue_edge: 'bg-orange-100 text-orange-800 border-orange-200',
  rest_advantage: 'bg-teal-100 text-teal-800 border-teal-200',
  schedule_pressure: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  playoff_context: 'bg-pink-100 text-pink-800 border-pink-200',
  season_trend: 'bg-gray-100 text-gray-800 border-gray-200',
};

const SIGNAL_LABELS: Record<string, string> = {
  odds_move: 'Odds Move',
  lineup_confirmed: 'Lineup',
  key_player_out: 'Player Out',
  matchup_trend: 'H2H Trend',
  segment_dominance: 'Segment Edge',
  fatigue_edge: 'Fatigue',
  rest_advantage: 'Rest Edge',
  schedule_pressure: 'Schedule',
  playoff_context: 'Playoff',
  season_trend: 'Trend',
};

export function SignalsBadge({ signals, compact = false }: Props) {
  if (signals.length === 0) return null;

  if (compact) {
    return (
      <div className="flex items-center gap-1 flex-wrap">
        <span className="text-xs text-gray-500">{signals.length} signals</span>
        {signals.slice(0, 3).map((s) => (
          <span
            key={s.id}
            className={cn(
              'inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium border',
              SIGNAL_COLORS[s.signal_type] || 'bg-gray-100 text-gray-600 border-gray-200',
            )}
            title={s.headline}
          >
            {SIGNAL_LABELS[s.signal_type] || s.signal_type}
          </span>
        ))}
        {signals.length > 3 && (
          <span className="text-[10px] text-gray-400">+{signals.length - 3}</span>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      <p className="text-xs font-semibold text-gray-700">Intelligence Signals</p>
      {signals.map((s) => (
        <div
          key={s.id}
          className={cn(
            'flex items-start gap-2 px-2.5 py-1.5 rounded-md border text-xs',
            SIGNAL_COLORS[s.signal_type] || 'bg-gray-50 text-gray-600 border-gray-200',
          )}
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="font-semibold">
                {SIGNAL_LABELS[s.signal_type] || s.signal_type}
              </span>
              <span className="text-[10px] opacity-70">
                str: {(s.signal_strength * 100).toFixed(0)}%
              </span>
            </div>
            <p className="text-[11px] opacity-80 truncate">{s.headline}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
