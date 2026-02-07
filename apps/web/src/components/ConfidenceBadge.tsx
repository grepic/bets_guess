import { formatProb } from '@/lib/utils';

interface Props {
  low: number;
  high: number;
  prob: number;
}

export function ConfidenceBadge({ low, high, prob }: Props) {
  // Visual bar showing interval
  const barLeft = low * 100;
  const barWidth = (high - low) * 100;
  const dotPos = prob * 100;

  return (
    <div className="mt-2">
      <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
        <span>95% CI</span>
        <span>{formatProb(low)} - {formatProb(high)}</span>
      </div>
      <div className="relative h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="absolute h-full bg-brand-200 rounded-full"
          style={{ left: `${barLeft}%`, width: `${barWidth}%` }}
        />
        <div
          className="absolute h-full w-1 bg-brand-600 rounded-full"
          style={{ left: `${dotPos}%` }}
        />
      </div>
    </div>
  );
}
