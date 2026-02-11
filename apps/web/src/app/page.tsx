'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchBestBets } from '@/lib/api';
import { getToday, getTomorrow, sportIcon, sportLabel } from '@/lib/utils';
import type { BestBet, FilterState, Sport } from '@/types';
import { FilterBlock } from '@/components/FilterBlock';
import { BetCard } from '@/components/BetCard';
import { BetListSkeleton } from '@/components/Skeleton';

type Tab = 'today' | 'tomorrow' | 'custom';

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('today');
  const [filters, setFilters] = useState<FilterState>({
    date: getToday(),
    sport: '',
    league: '',
    marketGroup: '',
    minEdge: 2,
    minProb: 0,
    minConf: 0,
    hideNoOdds: false,
  });

  const effectiveDate = activeTab === 'today' ? getToday() : activeTab === 'tomorrow' ? getTomorrow() : filters.date;

  const { data, isLoading, error } = useQuery({
    queryKey: ['best-bets', effectiveDate, filters.sport, filters.marketGroup, filters.minEdge, filters.minProb, filters.hideNoOdds],
    queryFn: () =>
      fetchBestBets({
        date: effectiveDate,
        sport: filters.sport || undefined,
        market_group: filters.marketGroup || undefined,
        min_edge: String(filters.minEdge),
        min_prob: String(filters.minProb),
        hide_no_odds: filters.hideNoOdds ? 'true' : undefined,
        limit: '100',
      }),
  });

  const bets: BestBet[] = data?.bets || [];

  // Group bets by sport
  const grouped: Record<string, BestBet[]> = {};
  bets.forEach((b) => {
    const key = b.sport;
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(b);
  });

  return (
    <div className="flex flex-col lg:flex-row gap-4 lg:gap-6">
      {/* Filters */}
      <aside className="lg:w-64 flex-shrink-0">
        <FilterBlock
          filters={{ ...filters, date: effectiveDate }}
          onChange={(f) => {
            setFilters(f);
            setActiveTab('custom');
          }}
        />
      </aside>

      {/* Main content */}
      <div className="flex-1 min-w-0">
        {/* Tab bar + count */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-4">
          <div className="flex items-center gap-1 bg-gray-100 p-1 rounded-lg">
            {(['today', 'tomorrow', 'custom'] as Tab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all duration-150 ${
                  activeTab === tab
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab === 'today' ? 'Today' : tab === 'tomorrow' ? 'Tomorrow' : 'Custom'}
              </button>
            ))}
          </div>
          <div className="text-sm text-gray-500 sm:ml-auto">
            <span className="font-bold text-gray-900">{bets.length}</span> value bets found
          </div>
        </div>

        {/* Disclaimer banner */}
        <div className="bg-amber-50/80 border border-amber-200/80 rounded-xl px-4 py-2.5 mb-4">
          <p className="text-xs text-amber-800">
            <strong>Disclaimer:</strong> Probabilities are model estimates, NOT guarantees.
            All betting involves risk. Never bet more than you can afford to lose.
          </p>
        </div>

        {/* Loading */}
        {isLoading && <BetListSkeleton />}

        {/* Error */}
        {error && (
          <div className="card p-8 text-center animate-fade-in">
            <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-danger-50 flex items-center justify-center">
              <svg className="w-6 h-6 text-danger-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <p className="text-red-600 text-sm font-semibold">Failed to load predictions</p>
            <p className="text-xs text-gray-500 mt-1">Make sure the backend is running on port 8000</p>
          </div>
        )}

        {/* Empty */}
        {!isLoading && !error && bets.length === 0 && (
          <div className="card p-10 text-center animate-fade-in">
            <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-gray-100 flex items-center justify-center">
              <svg className="w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <p className="text-gray-500 font-medium">No value bets found</p>
            <p className="text-xs text-gray-400 mt-1">Try lowering the minimum edge or changing the date.</p>
          </div>
        )}

        {/* Bet cards grouped by sport */}
        {Object.entries(grouped).map(([sport, sportBets]) => (
          <div key={sport} className="mb-6 animate-fade-in">
            <div className="flex items-center gap-2.5 mb-3">
              <span className="text-lg">{sportIcon(sport)}</span>
              <h2 className="section-title">{sportLabel(sport)}</h2>
              <span className="badge-sm bg-gray-100 text-gray-600 border-gray-200">
                {sportBets.length}
              </span>
            </div>
            <div className="grid gap-3 grid-cols-1 md:grid-cols-2">
              {sportBets.map((bet, idx) => (
                <BetCard key={`${bet.game_id}-${bet.market_spec.market_group}-${idx}`} bet={bet} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
