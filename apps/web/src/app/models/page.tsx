'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchBacktestReport, fetchSports } from '@/lib/api';
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
  { value: 'soccer_cards_total', label: 'Cards' },
  { value: 'nba_totals', label: 'NBA Totals' },
  { value: 'nba_player_points', label: 'NBA Player Points' },
  { value: 'nhl_totals', label: 'NHL Totals' },
  { value: 'tennis_winner', label: 'Tennis Winner' },
];

function MetricsCard({ title, metrics }: { title: string; metrics: BacktestMetrics }) {
  return (
    <div className="card p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">{title}</h3>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Stat label="Total Bets" value={String(metrics.total_bets)} />
        <Stat label="Win Rate" value={`${(metrics.win_rate * 100).toFixed(1)}%`} />
        <Stat
          label="ROI"
          value={`${metrics.roi_pct >= 0 ? '+' : ''}${metrics.roi_pct.toFixed(1)}%`}
          color={metrics.roi_pct >= 0 ? 'text-green-600' : 'text-red-600'}
        />
        <Stat label="Max Drawdown" value={`${metrics.max_drawdown.toFixed(1)} units`} />
        <Stat label="Avg Edge" value={`${metrics.avg_edge.toFixed(1)}%`} />
        {metrics.log_loss !== null && <Stat label="Log Loss" value={metrics.log_loss.toFixed(4)} />}
        {metrics.brier_score !== null && <Stat label="Brier Score" value={metrics.brier_score.toFixed(4)} />}
        {metrics.calibration_error !== null && (
          <Stat label="Calibration Error" value={metrics.calibration_error.toFixed(4)} />
        )}
      </div>
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`text-sm font-bold ${color || 'text-gray-900'}`}>{value}</p>
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
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Model Performance</h1>
      <p className="text-sm text-gray-500 mb-6">
        Backtest results and calibration metrics. Past performance does not guarantee future results.
      </p>

      {/* Sport/Market counts */}
      {sportsData && (
        <div className="grid grid-cols-4 gap-3 mb-6">
          {sportsData.sports.map((s: any) => (
            <div key={s.id} className="card p-3 text-center">
              <p className="text-lg font-bold text-brand-700">{s.market_count}</p>
              <p className="text-xs text-gray-500">{s.name} Markets</p>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-3 mb-6">
        <select
          value={sport}
          onChange={(e) => setSport(e.target.value)}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-md"
        >
          {SPORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <select
          value={marketGroup}
          onChange={(e) => setMarketGroup(e.target.value)}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-md"
        >
          {MARKET_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      {isLoading && (
        <div className="space-y-4">
          <div className="skeleton h-40 rounded-lg" />
          <div className="skeleton h-40 rounded-lg" />
        </div>
      )}

      {error && (
        <div className="card p-6 text-center text-red-600 text-sm">
          Failed to load backtest report. Is the API running?
        </div>
      )}

      {report && (
        <>
          {/* Disclaimer */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2.5 mb-4">
            <p className="text-xs text-amber-800">
              <strong>Note:</strong> {data?.disclaimer}
            </p>
          </div>

          {/* Report header */}
          <div className="card p-4 mb-4">
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-xs text-gray-500">Sport / League</p>
                <p className="font-semibold">{report.sport} / {report.league}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Market Group</p>
                <p className="font-semibold">{report.market_group}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Sample Size</p>
                <p className="font-semibold">{report.sample_size} bets</p>
              </div>
            </div>
          </div>

          {/* Flat Stake */}
          <div className="space-y-4">
            <MetricsCard title="Flat Stake (1 unit)" metrics={report.flat_stake} />
            {report.kelly_stake && (
              <MetricsCard title="Quarter Kelly (capped 5%)" metrics={report.kelly_stake} />
            )}
          </div>

          {/* Notes */}
          {report.notes && (
            <div className="mt-4 text-xs text-gray-500 italic">
              {report.notes}
            </div>
          )}
        </>
      )}
    </div>
  );
}
