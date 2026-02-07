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
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <span className="text-sm font-semibold text-gray-700">{title}</span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">{predictions.length} outcomes</span>
          <svg
            className={cn('w-4 h-4 text-gray-400 transition-transform', open && 'rotate-180')}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {open && (
        <div className="divide-y divide-gray-100">
          {predictions.map((pred, idx) => (
            <div key={idx} className="px-4 py-2.5 flex items-center justify-between hover:bg-gray-50">
              <div>
                <p className="text-sm font-medium text-gray-900">{pred.outcome_label}</p>
                <p className="text-xs text-gray-500">{pred.market_group}</p>
              </div>
              <div className="flex items-center gap-4 text-sm">
                <div className="text-right">
                  <p className="font-semibold">{formatProb(pred.probability)}</p>
                  <p className="text-xs text-gray-500">prob</p>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-brand-700">{formatOdds(pred.fair_odds)}</p>
                  <p className="text-xs text-gray-500">fair odds</p>
                </div>
                <div className="text-right text-xs text-gray-400">
                  {formatProb(pred.interval[0])}-{formatProb(pred.interval[1])}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
