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
    <div className="container-narrow animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight">Odds Moves</h1>
        <p className="section-subtitle mt-1">
          Significant odds movements detected across bookmakers. Shown when implied probability shifts by 3pp+.
        </p>
      </div>

      {/* Disclaimer */}
      <div className="bg-amber-50/80 border border-amber-200/80 rounded-xl px-4 py-2.5 mb-6">
        <p className="text-xs text-amber-800">
          <strong>Disclaimer:</strong> Odds movements are informational signals, NOT recommendations.
          Line movements occur for many reasons. Always do your own research.
        </p>
      </div>

      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="card p-4 sm:p-5 animate-pulse">
              <div className="flex justify-between mb-3">
                <div>
                  <div className="h-4 bg-gray-200 rounded w-48 mb-1.5" />
                  <div className="h-3 bg-gray-100 rounded w-32" />
                </div>
                <div className="h-5 w-20 bg-gray-200 rounded-full" />
              </div>
              <div className="grid grid-cols-4 gap-2">
                {[1, 2, 3, 4].map((j) => (
                  <div key={j} className="h-10 bg-gray-100 rounded-lg" />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {error && (
        <div className="card p-8 text-center">
          <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-danger-50 flex items-center justify-center">
            <svg className="w-6 h-6 text-danger-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <p className="text-red-600 text-sm font-semibold">Failed to load odds moves</p>
          <p className="text-xs text-gray-500 mt-1">Make sure the backend is running on port 8000</p>
        </div>
      )}

      {!isLoading && !error && moves.length === 0 && (
        <div className="card p-10 text-center">
          <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-gray-100 flex items-center justify-center">
            <svg className="w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <p className="text-gray-500 font-medium">No significant odds movements</p>
          <p className="text-xs text-gray-400 mt-1">
            Movements appear when bookmaker odds shift by 3pp+ implied probability.
          </p>
        </div>
      )}

      {moves.length > 0 && (
        <div className="space-y-3">
          {moves.map((move: any, idx: number) => {
            const isShortened = move.delta_implied_prob > 0;
            return (
              <div key={idx} className="card p-4 sm:p-5 animate-fade-in">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2 mb-3">
                  <div className="min-w-0">
                    <p className="text-sm font-bold text-gray-900 truncate">
                      {move.market_key.replace(/_/g, ' ')} &mdash; {move.outcome_label}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {move.bookmaker} &middot; Game: {move.game_id}
                    </p>
                  </div>
                  <span
                    className={cn(
                      'badge flex-shrink-0',
                      isShortened
                        ? 'bg-red-50 text-red-700 border-red-200'
                        : 'bg-green-50 text-green-700 border-green-200',
                    )}
                  >
                    {isShortened ? 'Shortened' : 'Drifted'}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3">
                  <div className="p-2.5 bg-gray-50 rounded-lg text-center">
                    <p className="stat-label">Old Odds</p>
                    <p className="stat-value font-mono">{formatOdds(move.old_price)}</p>
                  </div>
                  <div className="p-2.5 bg-gray-50 rounded-lg text-center">
                    <p className="stat-label">New Odds</p>
                    <p className="stat-value font-mono">{formatOdds(move.new_price)}</p>
                  </div>
                  <div className="p-2.5 bg-gray-50 rounded-lg text-center">
                    <p className="stat-label">Old Impl.</p>
                    <p className="stat-value">{formatProb(move.old_implied_prob)}</p>
                  </div>
                  <div className="p-2.5 bg-gray-50 rounded-lg text-center">
                    <p className="stat-label">Delta</p>
                    <p
                      className={cn(
                        'stat-value',
                        isShortened ? 'text-red-600' : 'text-green-600',
                      )}
                    >
                      {move.delta_implied_prob > 0 ? '+' : ''}
                      {(move.delta_implied_prob * 100).toFixed(1)}pp
                    </p>
                  </div>
                </div>

                {move.old_line !== null && move.new_line !== null && move.old_line !== move.new_line && (
                  <div className="mt-2 pt-2 border-t border-gray-100">
                    <p className="text-xs text-gray-500">
                      Line moved: <span className="font-mono font-medium text-gray-700">{move.old_line}</span>
                      {' '}&rarr;{' '}
                      <span className="font-mono font-medium text-gray-700">{move.new_line}</span>
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
