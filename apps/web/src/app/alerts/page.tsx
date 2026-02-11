'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchNotificationRules,
  fetchNotificationsSent,
  createNotificationRule,
} from '@/lib/api';
import { cn, formatTime } from '@/lib/utils';

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
    <div className="container-narrow animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight">Alerts & Notifications</h1>
        <p className="section-subtitle mt-1">
          Configure rules to get notified when intelligence signals align with value bets.
        </p>
      </div>

      {/* Disclaimer */}
      <div className="bg-amber-50/80 border border-amber-200/80 rounded-xl px-4 py-2.5 mb-6">
        <p className="text-xs text-amber-800">
          <strong>Disclaimer:</strong> Alerts are based on statistical signals, NOT guarantees.
          Always verify information independently. Bet responsibly.
        </p>
      </div>

      {/* Rules section */}
      <section className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <h2 className="section-title">Your Alert Rules</h2>
          <button
            onClick={handleCreateDefault}
            disabled={createMutation.isPending}
            className="btn-primary"
          >
            {createMutation.isPending ? (
              <>
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Creating...
              </>
            ) : (
              'Create Default Rule'
            )}
          </button>
        </div>

        {loadingRules && (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="card p-4 animate-pulse">
                <div className="h-5 bg-gray-200 rounded w-24 mb-2" />
                <div className="h-3 bg-gray-100 rounded w-48" />
              </div>
            ))}
          </div>
        )}

        {rules.length === 0 && !loadingRules && (
          <div className="card p-8 sm:p-10 text-center">
            <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-gray-100 flex items-center justify-center">
              <svg className="w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
            </div>
            <p className="text-gray-500 font-medium">No alert rules configured</p>
            <p className="text-xs text-gray-400 mt-1">
              Create a rule to get notified when signals align with value opportunities.
            </p>
          </div>
        )}

        {rules.length > 0 && (
          <div className="space-y-3">
            {rules.map((rule: any) => (
              <div key={rule.id} className="card p-4 sm:p-5 animate-fade-in">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-bold text-gray-700">
                    Rule #{rule.id}
                  </span>
                  <span
                    className={cn(
                      'badge',
                      rule.enabled
                        ? 'bg-green-50 text-green-700 border-green-200'
                        : 'bg-gray-100 text-gray-600 border-gray-200',
                    )}
                  >
                    {rule.enabled ? 'Active' : 'Disabled'}
                  </span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-2.5 bg-gray-50 rounded-lg">
                    <p className="stat-label">Min Edge</p>
                    <p className="stat-value">{rule.min_edge}%</p>
                  </div>
                  <div className="p-2.5 bg-gray-50 rounded-lg">
                    <p className="stat-label">Cooldown</p>
                    <p className="stat-value">{rule.cooldown_minutes}min</p>
                  </div>
                  <div className="p-2.5 bg-gray-50 rounded-lg">
                    <p className="stat-label">Max / Day</p>
                    <p className="stat-value">{rule.max_alerts_per_day}</p>
                  </div>
                  <div className="p-2.5 bg-gray-50 rounded-lg">
                    <p className="stat-label">Max / Game</p>
                    <p className="stat-value">{rule.max_alerts_per_game}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Sent notifications */}
      <section>
        <h2 className="section-title mb-4">Recent Notifications</h2>

        {loadingSent && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="card p-4 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-2" />
                <div className="h-3 bg-gray-100 rounded w-1/3" />
              </div>
            ))}
          </div>
        )}

        {notifications.length === 0 && !loadingSent && (
          <div className="card p-8 sm:p-10 text-center">
            <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-gray-100 flex items-center justify-center">
              <svg className="w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
            </div>
            <p className="text-gray-500 font-medium">No notifications sent yet</p>
            <p className="text-xs text-gray-400 mt-1">
              Alerts trigger when 2+ distinct signal types align for a game.
            </p>
          </div>
        )}

        {notifications.length > 0 && (
          <div className="space-y-3">
            {notifications.map((notif: any) => (
              <div key={notif.id} className="card p-4 sm:p-5 animate-fade-in">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2 mb-2">
                  <div className="min-w-0">
                    <p className="text-sm font-bold text-gray-900 truncate">
                      {notif.market_key} &mdash; {notif.selection}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Game: {notif.game_id} &middot; {formatTime(notif.sent_at)}
                    </p>
                  </div>
                  <span className="badge bg-green-50 text-green-700 border-green-200 flex-shrink-0">
                    +{notif.edge_pct.toFixed(1)}% edge
                  </span>
                </div>
                {notif.signals_summary.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2 pt-2 border-t border-gray-100">
                    {notif.signals_summary.map((sig: any, i: number) => (
                      <span
                        key={i}
                        className="badge-sm bg-blue-50 text-blue-700 border-blue-200"
                        title={sig.headline}
                      >
                        {sig.type.replace(/_/g, ' ')}
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
