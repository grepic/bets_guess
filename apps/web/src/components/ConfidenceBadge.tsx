import { formatProb } from '@/lib/utils';

interface Props {
  low: number;
  high: number;
  prob: number;
}

export function ConfidenceBadge({ low, high, prob }: Props) {
  const barLeft = Math.max(0, low * 100);
  const barWidth = Math.max(1, (high - low) * 100);
  const dotPos = prob * 100;

  return (
    <div className="mt-2">
      <div className="flex items-center justify-between text-[11px] font-medium text-gray-500 mb-1.5">
        <span className="uppercase tracking-wider">95% Confidence</span>
        <span className="font-mono text-gray-600">{formatProb(low)} - {formatProb(high)}</span>
      </div>
      <div className="relative h-2.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="absolute h-full bg-brand-200/80 rounded-full transition-all duration-300"
          style={{ left: `${barLeft}%`, width: `${barWidth}%` }}
        />
        <div
          className="absolute top-0 h-full w-1 bg-brand-600 rounded-full shadow-sm transition-all duration-300"
          style={{ left: `${dotPos}%` }}
        />
      </div>
    </div>
  );
}
