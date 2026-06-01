import React from 'react';
import { useRiskAlerts } from '../../hooks/useApi.js';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import { formatDate } from '../../utils/formatters.js';
import { ALERT_PRIORITY_COLORS } from '../../utils/constants.js';

export default function RiskAlertsView() {
  const { data, isLoading, error } = useRiskAlerts();

  if (isLoading) return <LoadingSpinner size="page" />;
  if (error)     return <div className="p-8 text-red-600">Failed to load alerts.</div>;

  const alerts = data?.data || [];

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Risk Alerts ({alerts.length})</h1>

      {alerts.length === 0 ? (
        <div className="card text-center py-12 text-gray-400">No active risk alerts.</div>
      ) : (
        <div className="space-y-3">
          {alerts.map((a) => (
            <div key={a.alert_id} className={`card border-l-4 ${
              a.priority === 'critical' ? 'border-l-red-500' :
              a.priority === 'high'     ? 'border-l-orange-500' :
              a.priority === 'medium'   ? 'border-l-amber-500' :
                                          'border-l-blue-500'
            }`}>
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs font-bold uppercase px-2 py-0.5 rounded ${ALERT_PRIORITY_COLORS[a.priority] || 'bg-gray-100 text-gray-700'}`}>
                      {a.priority}
                    </span>
                    <span className="text-xs text-gray-500">{a.alert_type?.replace('_', ' ')}</span>
                  </div>
                  <p className="text-sm text-gray-900">{a.message}</p>
                  <p className="text-xs text-gray-400 mt-1">Client: {a.client_name || a.client_id?.slice(0, 8)} · {formatDate(a.created_at)}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
