const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchApi<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(path, API_BASE);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v) url.searchParams.set(k, v);
    });
  }
  const res = await fetch(url.toString());
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function fetchGames(params: {
  date?: string;
  sport?: string;
  league?: string;
}) {
  return fetchApi<{ count: number; games: any[] }>('/games', params as Record<string, string>);
}

export async function fetchGame(gameId: string) {
  return fetchApi<any>(`/games/${gameId}`);
}

export async function fetchOdds(gameId: string) {
  return fetchApi<{ game_id: string; count: number; odds: any[] }>('/odds', { game_id: gameId });
}

export async function fetchPredictions(params: {
  date?: string;
  sport?: string;
  market_group?: string;
  min_edge?: string;
}) {
  return fetchApi<{ count: number; predictions: any[]; disclaimer: string }>(
    '/predictions',
    params as Record<string, string>,
  );
}

export async function fetchBestBets(params: {
  date?: string;
  sport?: string;
  league?: string;
  market_group?: string;
  min_edge?: string;
  min_conf?: string;
  min_prob?: string;
  hide_no_odds?: string;
  limit?: string;
}) {
  return fetchApi<{ count: number; bets: any[]; disclaimer: string; responsible_gambling: string }>(
    '/best-bets',
    params as Record<string, string>,
  );
}

export async function fetchMarketCatalog(sport?: string) {
  return fetchApi<{ total: number; markets: any[] }>('/catalog/markets', sport ? { sport } : undefined);
}

export async function fetchSports() {
  return fetchApi<{ sports: any[]; total_markets: number }>('/catalog/sports');
}

export async function fetchBacktestReport(params: {
  sport?: string;
  league?: string;
  market_group?: string;
}) {
  return fetchApi<{ report: any; disclaimer: string }>(
    '/reports/backtest',
    params as Record<string, string>,
  );
}

export async function fetchBuilderSuggestions(gameId: string) {
  return fetchApi<{ game_id: string; count: number; suggestions: any[]; disclaimer: string }>(
    '/builder/suggestions',
    { game_id: gameId },
  );
}

// ────────────────────────────────────────────────────────────
// Intelligence Signals & Alerts API
// ────────────────────────────────────────────────────────────

export async function fetchSignals(params: {
  game_id?: string;
  signal_type?: string;
  limit?: string;
}) {
  return fetchApi<{ count: number; signals: any[]; disclaimer: string }>(
    '/signals',
    params as Record<string, string>,
  );
}

export async function fetchOddsMoves(params: {
  game_id?: string;
  min_delta?: string;
  limit?: string;
}) {
  return fetchApi<{ count: number; moves: any[]; disclaimer: string }>(
    '/odds/moves',
    params as Record<string, string>,
  );
}

export async function fetchAdjustedPredictions(params: {
  game_id?: string;
  market_key?: string;
  min_edge?: string;
  limit?: string;
}) {
  return fetchApi<{ count: number; predictions: any[]; disclaimer: string }>(
    '/predictions/adjusted',
    params as Record<string, string>,
  );
}

export async function fetchNotificationRules(userKey?: string) {
  return fetchApi<{ count: number; rules: any[] }>(
    '/notifications/rules',
    userKey ? { user_key: userKey } : undefined,
  );
}

export async function createNotificationRule(rule: Record<string, any>) {
  const url = new URL('/notifications/rules', API_BASE);
  const res = await fetch(url.toString(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(rule),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchNotificationsSent(params: {
  user_key?: string;
  game_id?: string;
  limit?: string;
}) {
  return fetchApi<{ count: number; notifications: any[]; disclaimer: string }>(
    '/notifications/sent',
    params as Record<string, string>,
  );
}
