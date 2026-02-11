'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchBacktestReport, fetchSports } from '@/lib/api';
import { cn } from '@/lib/utils';
import type { BacktestMetrics } from '@/types';

const SPORT_OPTIONS = [
  { value: 'soccer', label: 'Soccer' },
  { value: 'nba', label: 'NBA' },
  { value: 'nhl', label: 'NHL' },
  { value: 'tennis', label: 'Tennis' },
];

const MARKET_OPTIONS = [
  { value: 'totals', label: 'Totals O/U' },
  { value: 'soccer_1x2_ft', label: '1X2' },
  { value: 'soccer_corners_total', label: 'Corners' },
  { value: 'nba_totals', label: 'NBA Totals' },
  { value: 'nhl_totals', label: 'NHL Totals' },
  { value: 'tennis_winner', label: 'Tennis Winner' },
];

function MetricsCard({ title, metrics }: { title: string; metrics: BacktestMetrics }) {
  return (
    <div className="card p-4 sm:p-5">
      <h3 className="text-sm font-bold text-gray-700 mb-3">{title}</h3>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Stat label="Total Bets" value={String(metrics.total_bets)} />
        <Stat label="Win Rate" value={`${(metrics.win_rate * 100).toFixed(1)}%`} />
        <Stat
          label="ROI"
          value={`${metrics.roi_pct >= 0 ? '+' : ''}${metrics.roi_pct.toFixed(1)}%`}
          color={metrics.roi_pct >= 0 ? 'text-green-600' : 'text-red-600'}
        />
        <Stat label="Max Drawdown" value={`${metrics.max_drawdown.toFixed(1)}u`} />
        <Stat label="Avg Edge" value={`${metrics.avg_edge.toFixed(1)}%`} />
        {metrics.log_loss !== null && <Stat label="Log Loss" value={metrics.log_loss.toFixed(4)} />}
        {metrics.brier_score !== null && <Stat label="Brier" value={metrics.brier_score.toFixed(4)} />}
        {metrics.calibration_error !== null && <Stat label="Cal. Error" value={metrics.calibration_error.toFixed(4)} />}
      </div>
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="p-2.5 bg-gray-50 rounded-lg">
      <p className="stat-label">{label}</p>
      <p className={cn('stat-value', color)}>{value}</p>
    </div>
  );
}

export default function ModelsPage() {
  const [sport, setSport] = useState('soccer');
  const [marketGroup, setMarketGroup] = useState('totals');

  const { data: sportsData } = useQuery({
    queryKey: ['sports'],
    queryFn: fetchSports,
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ['backtest', sport, marketGroup],
    queryFn: () => fetchBacktestReport({ sport, market_group: marketGroup }),
  });

  const report = data?.report;

  return (
    <div className="container-narrow animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight">Model Performance</h1>
        <p className="section-subtitle mt-1">
          Backtest results and calibration metrics. Past performance does not guarantee future results.
        </p>
      </div>

      {/* Sport cards */}
      {sportsData && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {sportsData.sports.map((s: any) => (
            <div
              key={s.id}
              className={cn(
                'card-interactive p-3 sm:p-4 text-center',
                sport === s.id && 'ring-2 ring-brand-500 border-brand-500',
              )}
              onClick={() => setSport(s.id)}
            >
              <p className="text-xl sm:text-2xl font-extrabold text-brand-700">{s.market_count}</p>
              <p className="text-xs text-gray-500 font-medium mt-0.5">{s.name} Markets</p>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <select value={sport} onChange={(e) => setSport(e.target.value)} className="select sm:w-auto">
          {SPORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <select value={marketGroup} onChange={(e) => setMarketGroup(e.target.value)} className="select sm:w-auto">
          {MARKET_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      {isLoading && (
        <div className="space-y-4 animate-pulse">
          <div className="h-40 bg-gray-100 rounded-xl" />
          <div className="h-40 bg-gray-100 rounded-xl" />
        </div>
      )}

      {error && (
        <div className="card p-8 text-center">
          <p className="text-red-600 text-sm font-semibold">Failed to load backtest report</p>
          <p className="text-xs text-gray-500 mt-1">Make sure the backend is running on port 8000</p>
        </div>
      )}

      {report && (
        <>
          <div className="bg-amber-50/80 border border-amber-200/80 rounded-xl px-4 py-2.5 mb-4">
            <p className="text-xs text-amber-800">
              <strong>Note:</strong> {data?.disclaimer}
            </p>
          </div>

          <div className="card p-4 sm:p-5 mb-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-2.5 bg-gray-50 rounded-lg">
                <p className="stat-label">Sport / League</p>
                <p className="stat-value">{report.sport} / {report.league}</p>
              </div>
              <div className="p-2.5 bg-gray-50 rounded-lg">
                <p className="stat-label">Market Group</p>
                <p className="stat-value">{report.market_group.replace(/_/g, ' ')}</p>
              </div>
              <div className="p-2.5 bg-gray-50 rounded-lg">
                <p className="stat-label">Sample Size</p>
                <p className="stat-value">{report.sample_size} bets</p>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <MetricsCard title="Flat Stake (1 unit)" metrics={report.flat_stake} />
            {report.kelly_stake && (
              <MetricsCard title="Quarter Kelly (capped 5%)" metrics={report.kelly_stake} />
            )}
          </div>

          {report.notes && (
            <p className="mt-4 text-xs text-gray-500 italic">{report.notes}</p>
          )}
        </>
      )}
    </div>
  );
}
