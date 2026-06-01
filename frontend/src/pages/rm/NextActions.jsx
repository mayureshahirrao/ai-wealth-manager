import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useNextActions } from '../../hooks/useApi.js';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';

const PRIORITY_STYLES = {
  critical: 'bg-red-100 text-red-700 border-red-200',
  high:     'bg-orange-100 text-orange-700 border-orange-200',
  medium:   'bg-amber-100 text-amber-700 border-amber-200',
  low:      'bg-blue-100 text-blue-700 border-blue-200',
};

const ACTION_ICONS = {
  REVIEW_OVERDUE:      '📅',
  CONCENTRATION_RISK:  '⚠️',
  GOAL_AT_RISK:        '🎯',
  KYC_EXPIRED:         '🪪',
  NO_NOMINEE:          '📋',
  NPS_NOT_OPENED:      '💰',
  FD_OVERWEIGHT:       '📉',
  ESTATE_GAP:          '📝',
  AI_LOW_CONFIDENCE:   '🤖',
  CRYPTO_OVERWEIGHT:   '₿',
};

export default function NextActions() {
  const { data, isLoading, error, refetch } = useNextActions();
  const navigate = useNavigate();
  const [filterPriority, setFilterPriority] = useState('all');

  if (isLoading) return <LoadingSpinner size="page" label="Loading action queue..." />;
  if (error) return (
    <div className="p-8 text-red-600">
      Failed to load actions.
      <button onClick={refetch} className="ml-2 underline text-blue-600">Retry</button>
    </div>
  );

  const result = data?.data || {};
  const allActions = result.actions || [];

  const filtered = filterPriority === 'all'
    ? allActions
    : allActions.filter(a => a.priority === filterPriority);

  const counts = {
    critical: allActions.filter(a => a.priority === 'critical').length,
    high:     allActions.filter(a => a.priority === 'high').length,
    medium:   allActions.filter(a => a.priority === 'medium').length,
    low:      allActions.filter(a => a.priority === 'low').length,
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Next Best Actions</h1>
          <p className="text-sm text-gray-500 mt-1">
            {allActions.length} action{allActions.length !== 1 ? 's' : ''} across all clients
            {result.generated_at && (
              <span className="ml-2 text-gray-400">
                · Updated {new Date(result.generated_at).toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <button onClick={refetch} className="btn-secondary text-sm">↻ Refresh</button>
      </div>

      {/* Priority filter chips */}
      <div className="flex gap-2 flex-wrap">
        {[
          { label: `All (${allActions.length})`, value: 'all' },
          { label: `Critical (${counts.critical})`, value: 'critical' },
          { label: `High (${counts.high})`, value: 'high' },
          { label: `Medium (${counts.medium})`, value: 'medium' },
          { label: `Low (${counts.low})`, value: 'low' },
        ].map(({ label, value }) => (
          <button
            key={value}
            onClick={() => setFilterPriority(value)}
            className={`px-3 py-1 rounded-full text-sm font-medium border transition-colors ${
              filterPriority === value
                ? 'bg-blue-600 text-white border-blue-600'
                : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Action list */}
      {filtered.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-4xl mb-3">✅</p>
          <p className="text-gray-600 font-medium">No pending actions</p>
          <p className="text-gray-400 text-sm mt-1">All clients are in good standing.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((action, idx) => (
            <div
              key={idx}
              className={`card border rounded-lg p-4 ${PRIORITY_STYLES[action.priority] || 'bg-gray-50 border-gray-200'}`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 flex-1">
                  <span className="text-xl">{ACTION_ICONS[action.action_type] || '📌'}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold uppercase tracking-wide">
                        {action.priority}
                      </span>
                      <span className="text-xs text-gray-500">·</span>
                      <span className="text-xs font-medium text-gray-600">
                        {action.action_type.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <p className="font-semibold text-gray-900 text-sm">{action.client_name}</p>
                    <p className="text-sm mt-1">{action.message}</p>
                    {action.recommended_action && (
                      <p className="text-xs mt-2 opacity-80 italic">
                        → {action.recommended_action}
                      </p>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => navigate(`/rm/clients/${action.client_id}`)}
                  className="shrink-0 text-xs font-medium text-blue-700 hover:underline whitespace-nowrap"
                >
                  View Client →
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
