'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { BestBet, IntelligenceSignal } from '@/types';
import {
  cn, edgeColor, formatEdge, formatOdds, formatProb,
  formatTime, riskColor, sportIcon, tagColor,
} from '@/lib/utils';
import { FactorList } from './FactorList';
import { ConfidenceBadge } from './ConfidenceBadge';
import { SignalsBadge } from './SignalsBadge';
import { fetchSignals } from '@/lib/api';

interface Props {
  bet: BestBet;
}

export function BetCard({ bet }: Props) {
  const [expanded, setExpanded] = useState(false);

  const { data: signalsData } = useQuery({
    queryKey: ['signals', bet.game_id],
    queryFn: () => fetchSignals({ game_id: bet.game_id }),
    staleTime: 5 * 60 * 1000,
  });

  const signals: IntelligenceSignal[] = signalsData?.signals || [];
  const tagLabel = bet.tag === 'high_conf' ? 'HIGH CONF' : bet.tag === 'longshot' ? 'LONGSHOT' : 'VALUE';

  return (
    <div className="card-hover p-4 sm:p-5 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="text-lg flex-shrink-0">{sportIcon(bet.sport)}</span>
          <div className="min-w-0">
            <p className="text-sm font-bold text-gray-900 truncate">
              {bet.home_team} vs {bet.away_team}
            </p>
            <p className="text-xs text-gray-500">
              {formatTime(bet.start_time)} &middot; {bet.league.toUpperCase()}
            </p>
          </div>
        </div>
        <span className={cn('badge flex-shrink-0', tagColor(bet.tag))}>
          {tagLabel}
        </span>
      </div>

      {/* Market + Outcome */}
      <div className="bg-gray-50 rounded-lg px-3.5 py-2.5 mb-3 border border-gray-100">
        <p className="text-[11px] font-medium text-gray-500 uppercase tracking-wider">{bet.market_name}</p>
        <p className="text-sm font-bold text-gray-900 mt-0.5">{bet.outcome_label}</p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
        <div className="text-center p-2 rounded-lg bg-gray-50/50">
          <p className="stat-label">Book Odds</p>
          <p className="stat-value font-mono">{formatOdds(bet.bookmaker_odds)}</p>
        </div>
        <div className="text-center p-2 rounded-lg bg-gray-50/50">
          <p className="stat-label">Model Prob</p>
          <p className="stat-value">{formatProb(bet.model_prob)}</p>
        </div>
        <div className="text-center p-2 rounded-lg bg-gray-50/50">
          <p className="stat-label">Fair Odds</p>
          <p className="stat-value text-brand-700 font-mono">{formatOdds(bet.fair_odds)}</p>
        </div>
        <div className="text-center p-2 rounded-lg bg-gray-50/50">
          <p className="stat-label">Edge</p>
          <p className={cn('stat-value', edgeColor(bet.edge_pct))}>
            {formatEdge(bet.edge_pct)}
          </p>
        </div>
      </div>

      {/* Confidence interval */}
      <ConfidenceBadge low={bet.interval_low} high={bet.interval_high} prob={bet.model_prob} />

      {/* Signals */}
      {signals.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <SignalsBadge signals={signals} compact />
        </div>
      )}

      {/* Risk */}
      {bet.risk_note && (
        <p className={cn('text-xs mt-2 font-medium', riskColor(bet.risk_level))}>
          {bet.risk_note}
        </p>
      )}

      {/* Expand factors */}
      {bet.factors.length > 0 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-3 text-xs text-brand-600 hover:text-brand-700 font-semibold transition-colors"
        >
          {expanded ? 'Hide factors' : `Show ${bet.factors.length} factors`}
        </button>
      )}

      {expanded && <FactorList factors={bet.factors} />}
    </div>
  );
}
