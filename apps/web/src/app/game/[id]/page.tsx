'use client';

import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { fetchGame, fetchPredictions, fetchBuilderSuggestions, fetchSignals } from '@/lib/api';
import { formatTime, sportIcon, formatOdds, formatProb } from '@/lib/utils';
import { MarketAccordion } from '@/components/MarketAccordion';
import { SignalsBadge } from '@/components/SignalsBadge';
import { GameDetailSkeleton } from '@/components/Skeleton';
import type { PredictionResult, IntelligenceSignal } from '@/types';

export default function GameDetailPage() {
  const params = useParams();
  const gameId = params.id as string;

  const { data: game, isLoading: loadingGame } = useQuery({
    queryKey: ['game', gameId],
    queryFn: () => fetchGame(gameId),
  });

  const { data: predData, isLoading: loadingPreds } = useQuery({
    queryKey: ['predictions', gameId],
    queryFn: () => fetchPredictions({ sport: game?.sport }),
    enabled: !!game,
  });

  const { data: builderData } = useQuery({
    queryKey: ['builder', gameId],
    queryFn: () => fetchBuilderSuggestions(gameId),
    enabled: !!game,
  });

  const { data: signalsData } = useQuery({
    queryKey: ['signals', gameId],
    queryFn: () => fetchSignals({ game_id: gameId }),
    enabled: !!game,
  });

  if (loadingGame || loadingPreds) return <GameDetailSkeleton />;
  if (!game) return (
    <div className="card p-10 text-center container-narrow">
      <p className="text-gray-500 font-medium">Game not found</p>
    </div>
  );

  const predictions: PredictionResult[] = (predData?.predictions || []).filter(
    (p: PredictionResult) => p.game_id === gameId,
  );
  const signals: IntelligenceSignal[] = signalsData?.signals || [];

  // Group predictions by market_group
  const grouped: Record<string, PredictionResult[]> = {};
  predictions.forEach((p) => {
    const group = p.market_group;
    if (!grouped[group]) grouped[group] = [];
    grouped[group].push(p);
  });

  const suggestions = builderData?.suggestions || [];

  return (
    <div className="container-narrow animate-fade-in">
      {/* Game header */}
      <div className="card p-5 sm:p-6 mb-4">
        <div className="flex items-center gap-3 sm:gap-4">
          <div className="w-12 h-12 rounded-xl bg-brand-50 flex items-center justify-center flex-shrink-0">
            <span className="text-2xl">{sportIcon(game.sport)}</span>
          </div>
          <div className="min-w-0">
            <h1 className="text-lg sm:text-xl font-extrabold text-gray-900 tracking-tight truncate">
              {game.home_team.name} vs {game.away_team.name}
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">
              {formatTime(game.start_time)} &middot; {game.league.toUpperCase()} &middot; {game.venue}
            </p>
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="bg-amber-50/80 border border-amber-200/80 rounded-xl px-4 py-2.5 mb-4">
        <p className="text-xs text-amber-800">
          <strong>Disclaimer:</strong> All probabilities are model estimates with uncertainty ranges.
          These are NOT guarantees. Bet responsibly.
        </p>
      </div>

      {/* Intelligence Signals */}
      {signals.length > 0 && (
        <div className="card p-4 sm:p-5 mb-4">
          <SignalsBadge signals={signals} />
        </div>
      )}

      {/* Market accordions */}
      <div className="space-y-3">
        {Object.entries(grouped).map(([group, preds]) => (
          <MarketAccordion
            key={group}
            title={group.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
            predictions={preds}
            defaultOpen={group.includes('1x2') || group.includes('moneyline') || group.includes('winner')}
          />
        ))}
      </div>

      {/* Bet builder suggestions */}
      {suggestions.length > 0 && (
        <div className="mt-6 sm:mt-8">
          <h2 className="section-title mb-3">Bet Builder Suggestions</h2>
          <div className="bg-amber-50/80 border border-amber-200/80 rounded-xl px-4 py-2 mb-3">
            <p className="text-xs text-amber-800">
              Combined bets carry significantly higher risk. Correlation adjustments are approximate.
              Never bet more than you can afford to lose.
            </p>
          </div>
          <div className="space-y-3">
            {suggestions.map((s: any, idx: number) => (
              <div key={idx} className="card p-4 sm:p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-bold text-gray-700">
                    {s.legs.length}-Leg Builder
                  </span>
                  <span className={`badge-sm ${s.compatible ? 'bg-green-50 text-green-700 border-green-200' : 'bg-gray-100 text-gray-600 border-gray-200'}`}>
                    {s.compatible ? 'Compatible' : 'Incompatible'}
                  </span>
                </div>
                <div className="space-y-1 mb-3">
                  {s.legs.map((leg: any, li: number) => (
                    <div key={li} className="text-xs text-gray-600 flex justify-between py-0.5">
                      <span className="truncate mr-2">{leg.outcome_label}</span>
                      <span className="font-mono font-medium flex-shrink-0">{formatProb(leg.individual_prob)}</span>
                    </div>
                  ))}
                </div>
                <div className="grid grid-cols-3 gap-3 text-center text-xs border-t border-gray-100 pt-3">
                  <div>
                    <p className="stat-label">Combined</p>
                    <p className="font-bold text-gray-900 mt-0.5">{formatProb(s.adjusted_prob)}</p>
                  </div>
                  <div>
                    <p className="stat-label">Fair Odds</p>
                    <p className="font-bold text-brand-700 font-mono mt-0.5">{formatOdds(s.adjusted_fair_odds)}</p>
                  </div>
                  <div>
                    <p className="stat-label">Corr. Adj.</p>
                    <p className="font-bold text-gray-900 mt-0.5">{(s.correlation_adjustment * 100).toFixed(1)}%</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
