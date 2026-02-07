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
    <div className="flex flex-col lg:flex-row gap-6">
      {/* Left: Filters */}
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
        {/* Tabs */}
        <div className="flex items-center gap-1 mb-4">
          {(['today', 'tomorrow', 'custom'] as Tab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                activeTab === tab
                  ? 'bg-brand-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
              }`}
            >
              {tab === 'today' ? 'Today' : tab === 'tomorrow' ? 'Tomorrow' : 'Custom'}
            </button>
          ))}
          <div className="ml-auto text-sm text-gray-500">
            {bets.length} value bets found
          </div>
        </div>

        {/* Disclaimer banner */}
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2.5 mb-4">
          <p className="text-xs text-amber-800">
            <strong>Disclaimer:</strong> Probabilities are model estimates, NOT guarantees.
            All betting involves risk. Never bet more than you can afford to lose.
          </p>
        </div>

        {/* Loading */}
        {isLoading && <BetListSkeleton />}

        {/* Error */}
        {error && (
          <div className="card p-6 text-center">
            <p className="text-red-600 text-sm">Failed to load predictions. Is the API running?</p>
            <p className="text-xs text-gray-500 mt-1">Make sure the backend is running on port 8000</p>
          </div>
        )}

        {/* Empty */}
        {!isLoading && !error && bets.length === 0 && (
          <div className="card p-8 text-center">
            <p className="text-gray-500">No value bets found matching your filters.</p>
            <p className="text-xs text-gray-400 mt-1">Try lowering the minimum edge or changing the date.</p>
          </div>
        )}

        {/* Bet cards grouped by sport */}
        {Object.entries(grouped).map(([sport, sportBets]) => (
          <div key={sport} className="mb-6">
            <h2 className="flex items-center gap-2 text-lg font-bold text-gray-800 mb-3">
              {sportIcon(sport)} {sportLabel(sport)}
              <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full font-normal">
                {sportBets.length}
              </span>
            </h2>
            <div className="grid gap-3 sm:grid-cols-1 md:grid-cols-2">
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
