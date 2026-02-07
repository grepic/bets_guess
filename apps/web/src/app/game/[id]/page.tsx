'use client';

import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { fetchGame, fetchPredictions, fetchBuilderSuggestions } from '@/lib/api';
import { formatTime, sportIcon, formatOdds, formatProb } from '@/lib/utils';
import { MarketAccordion } from '@/components/MarketAccordion';
import { GameDetailSkeleton } from '@/components/Skeleton';
import type { PredictionResult } from '@/types';

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

  if (loadingGame || loadingPreds) return <GameDetailSkeleton />;
  if (!game) return <div className="card p-8 text-center text-gray-500">Game not found</div>;

  const predictions: PredictionResult[] = (predData?.predictions || []).filter(
    (p: PredictionResult) => p.game_id === gameId,
  );

  // Group predictions by market_group
  const grouped: Record<string, PredictionResult[]> = {};
  predictions.forEach((p) => {
    const group = p.market_group;
    if (!grouped[group]) grouped[group] = [];
    grouped[group].push(p);
  });

  const suggestions = builderData?.suggestions || [];

  return (
    <div className="max-w-4xl mx-auto">
      {/* Game header */}
      <div className="card p-6 mb-6">
        <div className="flex items-center gap-3 mb-4">
          <span className="text-2xl">{sportIcon(game.sport)}</span>
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              {game.home_team.name} vs {game.away_team.name}
            </h1>
            <p className="text-sm text-gray-500">
              {formatTime(game.start_time)} &middot; {game.league.toUpperCase()} &middot; {game.venue}
            </p>
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2.5 mb-4">
        <p className="text-xs text-amber-800">
          <strong>Disclaimer:</strong> All probabilities are model estimates with uncertainty ranges.
          These are NOT guarantees. Bet responsibly.
        </p>
      </div>

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
        <div className="mt-8">
          <h2 className="text-lg font-bold text-gray-800 mb-3">Bet Builder Suggestions</h2>
          <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 mb-3">
            <p className="text-xs text-amber-800">
              Combined bets carry significantly higher risk. Correlation adjustments are approximate.
              Never bet more than you can afford to lose.
            </p>
          </div>
          <div className="space-y-3">
            {suggestions.map((s: any, idx: number) => (
              <div key={idx} className="card p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold text-gray-700">
                    {s.legs.length}-Leg Builder
                  </span>
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                    {s.compatible ? 'Compatible' : 'Incompatible'}
                  </span>
                </div>
                <div className="space-y-1 mb-2">
                  {s.legs.map((leg: any, li: number) => (
                    <div key={li} className="text-xs text-gray-600 flex justify-between">
                      <span>{leg.outcome_label}</span>
                      <span className="font-mono">{formatProb(leg.individual_prob)}</span>
                    </div>
                  ))}
                </div>
                <div className="grid grid-cols-3 gap-2 text-center text-xs border-t pt-2">
                  <div>
                    <p className="text-gray-500">Combined Prob</p>
                    <p className="font-semibold">{formatProb(s.adjusted_prob)}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Fair Odds</p>
                    <p className="font-semibold text-brand-700">{formatOdds(s.adjusted_fair_odds)}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Corr. Adj.</p>
                    <p className="font-semibold">{(s.correlation_adjustment * 100).toFixed(1)}%</p>
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
