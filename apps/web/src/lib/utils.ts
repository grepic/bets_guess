import { clsx, type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatOdds(odds: number): string {
  return odds.toFixed(2);
}

export function formatProb(prob: number): string {
  return `${(prob * 100).toFixed(1)}%`;
}

export function formatEdge(edge: number): string {
  const sign = edge >= 0 ? '+' : '';
  return `${sign}${edge.toFixed(1)}%`;
}

export function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });
}

export function formatTime(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function sportIcon(sport: string): string {
  const icons: Record<string, string> = {
    soccer: '\u26BD',
    nba: '\uD83C\uDFC0',
    nhl: '\uD83C\uDFD2',
    tennis: '\uD83C\uDFBE',
  };
  return icons[sport] || '\uD83C\uDFC6';
}

export function sportLabel(sport: string): string {
  const labels: Record<string, string> = {
    soccer: 'Soccer',
    nba: 'NBA',
    nhl: 'NHL',
    tennis: 'Tennis',
  };
  return labels[sport] || sport.toUpperCase();
}

export function tagColor(tag: string): string {
  switch (tag) {
    case 'high_conf':
      return 'bg-green-100 text-green-800 border-green-200';
    case 'value':
      return 'bg-amber-100 text-amber-800 border-amber-200';
    case 'longshot':
      return 'bg-purple-100 text-purple-800 border-purple-200';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200';
  }
}

export function riskColor(risk: string): string {
  switch (risk) {
    case 'low':
      return 'text-green-600';
    case 'medium':
      return 'text-amber-600';
    case 'high':
      return 'text-red-600';
    default:
      return 'text-gray-600';
  }
}

export function edgeColor(edge: number): string {
  if (edge >= 10) return 'text-green-600 font-bold';
  if (edge >= 5) return 'text-green-500';
  if (edge >= 2) return 'text-amber-500';
  return 'text-gray-500';
}

export function getToday(): string {
  return new Date().toISOString().slice(0, 10);
}

export function getTomorrow(): string {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return d.toISOString().slice(0, 10);
}
