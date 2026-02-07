import type { ExplanationFactor } from '@/types';

interface Props {
  factors: ExplanationFactor[];
}

export function FactorList({ factors }: Props) {
  if (!factors.length) return null;

  return (
    <div className="mt-3 space-y-1.5">
      <p className="text-xs font-semibold text-gray-500 uppercase">Key Factors</p>
      {factors.map((f, i) => (
        <div key={i} className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <div
              className="h-1.5 rounded-full bg-brand-500"
              style={{ width: `${Math.max(20, (f.importance || 0.1) * 100)}px` }}
            />
            <span className="text-gray-700">{f.name}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-mono font-medium text-gray-900">{f.value}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
