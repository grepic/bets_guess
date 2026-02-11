'use client';

import { useState } from 'react';
import type { PredictionResult } from '@/types';
import { cn, formatOdds, formatProb } from '@/lib/utils';

interface Props {
  title: string;
  predictions: PredictionResult[];
  defaultOpen?: boolean;
}

export function MarketAccordion({ title, predictions, defaultOpen = false }: Props) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="card overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 sm:px-5 py-3.5 bg-gray-50/50 hover:bg-gray-50 transition-colors"
      >
        <span className="text-sm font-bold text-gray-700">{title}</span>
        <div className="flex items-center gap-2">
          <span className="badge-sm bg-gray-100 text-gray-600 border-gray-200">
            {predictions.length}
          </span>
          <svg
            className={cn('w-4 h-4 text-gray-400 transition-transform duration-200', open && 'rotate-180')}
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {open && (
        <div className="divide-y divide-gray-100 animate-slide-down">
          {predictions.map((pred, idx) => (
            <div key={idx} className="px-4 sm:px-5 py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-gray-50/50 transition-colors">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-gray-900">{pred.outcome_label}</p>
                <p className="text-xs text-gray-500">{pred.market_group.replace(/_/g, ' ')}</p>
              </div>
              <div className="flex items-center gap-4 sm:gap-6 text-sm flex-shrink-0">
                <div className="text-center">
                  <p className="font-bold">{formatProb(pred.probability)}</p>
                  <p className="stat-label">prob</p>
                </div>
                <div className="text-center">
                  <p className="font-bold text-brand-700 font-mono">{formatOdds(pred.fair_odds)}</p>
                  <p className="stat-label">fair odds</p>
                </div>
                <div className="text-center hidden sm:block">
                  <p className="text-xs font-medium text-gray-500">
                    {formatProb(pred.interval[0])} - {formatProb(pred.interval[1])}
                  </p>
                  <p className="stat-label">95% CI</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
