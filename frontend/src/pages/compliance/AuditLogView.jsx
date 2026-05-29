import React from 'react';
import { useAuditLog } from '../../hooks/useApi.js';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import ConfidenceBadge from '../../components/ConfidenceBadge.jsx';
import { formatDate } from '../../utils/formatters.js';

export default function AuditLogView() {
  const { data, isLoading, error } = useAuditLog();

  if (isLoading) return <LoadingSpinner size="page" label="Loading audit log..." />;
  if (error)     return <div className="p-8 text-red-600">Failed to load audit log.</div>;

  const logs = data?.data || [];

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">AI Audit Log</h1>
        <p className="text-xs text-gray-500">SEBI IA Regulation — all AI interactions logged</p>
      </div>

      {logs.length === 0 ? (
        <div className="card text-center py-12 text-gray-400">No AI interactions logged yet.</div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Client</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tool</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Query</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Confidence</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">SEBI OK</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {logs.map((log) => (
                <tr key={log.log_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-500 whitespace-nowrap text-xs">{formatDate(log.created_at)}</td>
                  <td className="px-4 py-3 text-gray-600 font-mono text-xs">{log.client_id?.slice(0, 8)}...</td>
                  <td className="px-4 py-3">
                    <span className="bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded">{log.tool_name}</span>
                  </td>
                  <td className="px-4 py-3 text-gray-600 max-w-xs truncate">{log.user_query}</td>
                  <td className="px-4 py-3 text-center">
                    {log.confidence_score != null
                      ? <ConfidenceBadge score={log.confidence_score} showLabel={false} />
                      : <span className="text-gray-300">—</span>
                    }
                  </td>
                  <td className="px-4 py-3 text-center">
                    {log.sebi_compliant
                      ? <span className="text-green-600 text-xs font-medium">✓</span>
                      : <span className="text-red-600 text-xs font-medium">✗</span>
                    }
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
