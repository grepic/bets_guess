'use client';

import { useQuery } from '@tanstack/react-query';
import { fetchOddsMoves } from '@/lib/api';
import { cn, formatProb, formatOdds } from '@/lib/utils';

export default function OddsMovesPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['odds-moves'],
    queryFn: () => fetchOddsMoves({ limit: '100' }),
  });

  const moves = data?.moves || [];

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Odds Moves</h1>
      <p className="text-sm text-gray-500 mb-6">
        Significant odds movements detected across bookmakers. Movements shown when implied
        probability changes by 3pp or more.
      </p>

      {/* Disclaimer */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2.5 mb-6">
        <p className="text-xs text-amber-800">
          <strong>Disclaimer:</strong> Odds movements are informational signals, NOT recommendations.
          Line movements can occur for many reasons. Always do your own research.
        </p>
      </div>

      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card p-4 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-2/3 mb-2" />
              <div className="h-3 bg-gray-100 rounded w-1/2" />
            </div>
          ))}
        </div>
      )}

      {error && (
        <div className="card p-6 text-center">
          <p className="text-red-600 text-sm">Failed to load odds moves. Is the API running?</p>
        </div>
      )}

      {!isLoading && !error && moves.length === 0 && (
        <div className="card p-8 text-center">
          <p className="text-gray-500">No significant odds movements detected.</p>
          <p className="text-xs text-gray-400 mt-1">
            Movements will appear here when bookmaker odds shift by 3pp+ implied probability.
          </p>
        </div>
      )}

      {moves.length > 0 && (
        <div className="space-y-3">
          {moves.map((move: any, idx: number) => {
            const isShortened = move.delta_implied_prob > 0;
            return (
              <div key={idx} className="card p-4">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="text-sm font-semibold text-gray-700">
                      {move.market_key} — {move.outcome_label}
                    </p>
                    <p className="text-xs text-gray-500">
                      {move.bookmaker} &middot; Game: {move.game_id}
                    </p>
                  </div>
                  <span
                    className={cn(
                      'text-sm font-bold',
                      isShortened ? 'text-red-600' : 'text-green-600',
                    )}
                  >
                    {isShortened ? 'Shortened' : 'Drifted'}
                  </span>
                </div>

                <div className="grid grid-cols-4 gap-2 text-center text-xs">
                  <div>
                    <p className="text-gray-400">Old Odds</p>
                    <p className="font-semibold">{formatOdds(move.old_price)}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">New Odds</p>
                    <p className="font-semibold">{formatOdds(move.new_price)}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Old Impl.</p>
                    <p className="font-semibold">{formatProb(move.old_implied_prob)}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Delta</p>
                    <p
                      className={cn(
                        'font-bold',
                        isShortened ? 'text-red-600' : 'text-green-600',
                      )}
                    >
                      {move.delta_implied_prob > 0 ? '+' : ''}
                      {(move.delta_implied_prob * 100).toFixed(1)}pp
                    </p>
                  </div>
                </div>

                {move.old_line !== null && move.new_line !== null && move.old_line !== move.new_line && (
                  <p className="text-xs text-gray-500 mt-2">
                    Line moved: {move.old_line} &rarr; {move.new_line}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
