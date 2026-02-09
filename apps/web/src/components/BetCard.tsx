'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { BestBet, IntelligenceSignal } from '@/types';
import {
  cn, edgeColor, formatEdge, formatOdds, formatProb,
  formatTime, riskColor, sportIcon, sportLabel, tagColor,
} from '@/lib/utils';
import { fetchSignals } from '@/lib/api';
import { FactorList } from './FactorList';
import { ConfidenceBadge } from './ConfidenceBadge';
import { SignalsBadge } from './SignalsBadge';

interface Props {
  bet: BestBet;
}

export function BetCard({ bet }: Props) {
  const [expanded, setExpanded] = useState(false);

  const tagLabel = bet.tag === 'high_conf' ? 'HIGH CONF' : bet.tag === 'longshot' ? 'LONGSHOT' : 'VALUE';

  return (
    <div className="card-hover p-4">
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-base">{sportIcon(bet.sport)}</span>
          <div>
            <p className="text-sm font-semibold text-gray-900">
              {bet.home_team} vs {bet.away_team}
            </p>
            <p className="text-xs text-gray-500">
              {formatTime(bet.start_time)} &middot; {bet.league.toUpperCase()}
            </p>
          </div>
        </div>
        <span className={cn('badge', tagColor(bet.tag))}>
          {tagLabel}
        </span>
      </div>

      {/* Market + Outcome */}
      <div className="bg-gray-50 rounded-md px-3 py-2 mb-3">
        <p className="text-xs text-gray-500">{bet.market_name}</p>
        <p className="text-sm font-bold text-gray-900">{bet.outcome_label}</p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-2 text-center mb-3">
        <div>
          <p className="text-xs text-gray-500">Book Odds</p>
          <p className="text-sm font-semibold">{formatOdds(bet.bookmaker_odds)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Model Prob</p>
          <p className="text-sm font-semibold">{formatProb(bet.model_prob)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Fair Odds</p>
          <p className="text-sm font-semibold text-brand-700">{formatOdds(bet.fair_odds)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Edge</p>
          <p className={cn('text-sm font-bold', edgeColor(bet.edge_pct))}>
            {formatEdge(bet.edge_pct)}
          </p>
        </div>
      </div>

      {/* Confidence interval */}
      <ConfidenceBadge low={bet.interval_low} high={bet.interval_high} prob={bet.model_prob} />

      {/* Signals */}
      <GameSignals gameId={bet.game_id} />

      {/* Risk */}
      {bet.risk_note && (
        <p className={cn('text-xs mt-2', riskColor(bet.risk_level))}>
          {bet.risk_note}
        </p>
      )}

      {/* Expand factors */}
      {bet.factors.length > 0 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-3 text-xs text-brand-600 hover:text-brand-700 font-medium"
        >
          {expanded ? 'Hide factors' : `Show ${bet.factors.length} factors`}
        </button>
      )}

      {expanded && <FactorList factors={bet.factors} />}
    </div>
  );
}

function GameSignals({ gameId }: { gameId: string }) {
  const { data } = useQuery({
    queryKey: ['signals', gameId],
    queryFn: () => fetchSignals({ game_id: gameId, limit: '5' }),
    staleTime: 60_000,
  });

  const signals: IntelligenceSignal[] = data?.signals || [];
  if (signals.length === 0) return null;

  return (
    <div className="mt-2">
      <SignalsBadge signals={signals} compact />
    </div>
  );
}
