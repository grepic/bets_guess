import type { ExplanationFactor } from '@/types';

interface Props {
  factors: ExplanationFactor[];
}

export function FactorList({ factors }: Props) {
  if (!factors.length) return null;

  return (
    <div className="mt-3 pt-3 border-t border-gray-100 space-y-2 animate-slide-down">
      <p className="stat-label">Key Factors</p>
      {factors.map((f, i) => (
        <div key={i} className="flex items-center justify-between gap-3 text-xs group">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="flex-shrink-0 w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-brand-500 rounded-full transition-all duration-300"
                style={{ width: `${Math.max(15, (f.importance || 0.1) * 100)}%` }}
              />
            </div>
            <span className="text-gray-700 truncate group-hover:text-gray-900 transition-colors">{f.name}</span>
          </div>
          <span className="font-mono font-bold text-gray-900 flex-shrink-0">{f.value}</span>
        </div>
      ))}
    </div>
  );
}
