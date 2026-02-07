'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchNotificationRules,
  fetchNotificationsSent,
  createNotificationRule,
} from '@/lib/api';
import { formatTime } from '@/lib/utils';

export default function AlertsPage() {
  const queryClient = useQueryClient();
  const [userKey] = useState('demo-user');

  const { data: rulesData, isLoading: loadingRules } = useQuery({
    queryKey: ['notification-rules', userKey],
    queryFn: () => fetchNotificationRules(userKey),
  });

  const { data: sentData, isLoading: loadingSent } = useQuery({
    queryKey: ['notifications-sent', userKey],
    queryFn: () => fetchNotificationsSent({ user_key: userKey }),
  });

  const createMutation = useMutation({
    mutationFn: createNotificationRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-rules'] });
    },
  });

  const rules = rulesData?.rules || [];
  const notifications = sentData?.notifications || [];

  const handleCreateDefault = () => {
    createMutation.mutate({
      user_key: userKey,
      sports: [],
      leagues: [],
      market_groups: [],
      min_edge: 3.0,
      min_confidence: 0.0,
      min_prob: 0.0,
      quiet_hours: { start: '23:00', end: '07:00' },
      max_alerts_per_game: 3,
      max_alerts_per_day: 20,
      cooldown_minutes: 30,
      enabled: true,
    });
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Alerts & Notifications</h1>

      {/* Disclaimer */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2.5 mb-6">
        <p className="text-xs text-amber-800">
          <strong>Disclaimer:</strong> Alerts are based on statistical signals, NOT guarantees.
          Always verify information independently. Bet responsibly.
        </p>
      </div>

      {/* Rules section */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-800">Your Alert Rules</h2>
          <button
            onClick={handleCreateDefault}
            disabled={createMutation.isPending}
            className="px-4 py-2 bg-brand-600 text-white text-sm rounded-lg hover:bg-brand-700 disabled:opacity-50"
          >
            {createMutation.isPending ? 'Creating...' : 'Create Default Rule'}
          </button>
        </div>

        {loadingRules && <p className="text-sm text-gray-500">Loading rules...</p>}

        {rules.length === 0 && !loadingRules && (
          <div className="card p-6 text-center">
            <p className="text-gray-500 text-sm">No alert rules configured yet.</p>
            <p className="text-xs text-gray-400 mt-1">
              Create a rule to get notified when signals align with value opportunities.
            </p>
          </div>
        )}

        {rules.length > 0 && (
          <div className="space-y-3">
            {rules.map((rule: any) => (
              <div key={rule.id} className="card p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold text-gray-700">
                    Rule #{rule.id}
                  </span>
                  <span
                    className={`badge ${
                      rule.enabled
                        ? 'bg-green-100 text-green-800 border-green-200'
                        : 'bg-gray-100 text-gray-600 border-gray-200'
                    }`}
                  >
                    {rule.enabled ? 'Active' : 'Disabled'}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-3 text-xs text-gray-600">
                  <div>
                    <span className="text-gray-400">Min Edge:</span> {rule.min_edge}%
                  </div>
                  <div>
                    <span className="text-gray-400">Cooldown:</span> {rule.cooldown_minutes}min
                  </div>
                  <div>
                    <span className="text-gray-400">Max/Day:</span> {rule.max_alerts_per_day}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Sent notifications */}
      <section>
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Recent Notifications</h2>

        {loadingSent && <p className="text-sm text-gray-500">Loading notifications...</p>}

        {notifications.length === 0 && !loadingSent && (
          <div className="card p-6 text-center">
            <p className="text-gray-500 text-sm">No notifications sent yet.</p>
            <p className="text-xs text-gray-400 mt-1">
              Notifications require at least 2 distinct signal types for a game before triggering.
            </p>
          </div>
        )}

        {notifications.length > 0 && (
          <div className="space-y-3">
            {notifications.map((notif: any) => (
              <div key={notif.id} className="card p-4">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="text-sm font-semibold text-gray-700">
                      {notif.market_key} — {notif.selection}
                    </p>
                    <p className="text-xs text-gray-500">
                      Game: {notif.game_id} &middot; {formatTime(notif.sent_at)}
                    </p>
                  </div>
                  <span className="text-sm font-bold text-green-600">
                    +{notif.edge_pct.toFixed(1)}%
                  </span>
                </div>
                {notif.signals_summary.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {notif.signals_summary.map((sig: any, i: number) => (
                      <span
                        key={i}
                        className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-50 text-blue-700 border border-blue-200"
                        title={sig.headline}
                      >
                        {sig.type}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
