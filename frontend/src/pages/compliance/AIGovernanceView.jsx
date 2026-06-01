import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../../api/apiClient.js';
import { ENDPOINTS } from '../../api/endpoints.js';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import ConfidenceBadge from '../../components/ConfidenceBadge.jsx';
import { formatDate } from '../../utils/formatters.js';

function useAIGovernance(days) {
  return useQuery({
    queryKey: ['aiGovernance', days],
    queryFn: () => apiClient.get(ENDPOINTS.COMPLIANCE.AI_GOVERNANCE, { params: { days } }),
    staleTime: 60_000,
  });
}

function StatCard({ label, value, sub, color = 'text-gray-900' }) {
  return (
    <div className="card text-center">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  );
}

export default function AIGovernanceView() {
  const [days, setDays] = useState(30);
  const { data, isLoading, error } = useAIGovernance(days);

  if (isLoading) return <LoadingSpinner size="page" label="Loading AI governance metrics..." />;
  if (error) return <div className="p-8 text-red-600">Failed to load AI governance data.</div>;

  const d = data?.data;

  if (!d || d.total_interactions === 0) {
    return (
      <div className="p-6 space-y-4">
        <Header days={days} setDays={setDays} />
        <div className="card text-center py-12 text-gray-400">No AI interactions in this period.</div>
      </div>
    );
  }

  const complianceColor = d.sebi_compliance_rate_pct >= 95
    ? 'text-green-600' : d.sebi_compliance_rate_pct >= 80
    ? 'text-amber-600' : 'text-red-600';

  const confidenceColor = (d.average_confidence || 0) >= 0.75
    ? 'text-green-600' : (d.average_confidence || 0) >= 0.50
    ? 'text-amber-600' : 'text-red-600';

  const cd = d.confidence_distribution || {};

  return (
    <div className="p-6 space-y-6">
      <Header days={days} setDays={setDays} />

      {/* Summary flags */}
      {(d.flags?.non_compliant_count > 0 || d.flags?.interactions_below_threshold > 0) && (
        <div className="flex flex-wrap gap-3">
          {d.flags.non_compliant_count > 0 && (
            <div className="px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              ⚠ {d.flags.non_compliant_count} non-compliant interaction{d.flags.non_compliant_count !== 1 ? 's' : ''}
            </div>
          )}
          {d.flags.interactions_below_threshold > 0 && (
            <div className="px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-700">
              🔍 {d.flags.interactions_below_threshold} low-confidence interaction{d.flags.interactions_below_threshold !== 1 ? 's' : ''} need review
            </div>
          )}
          {d.flags.missing_disclaimer_count > 0 && (
            <div className="px-3 py-2 bg-orange-50 border border-orange-200 rounded-lg text-sm text-orange-700">
              📋 {d.flags.missing_disclaimer_count} interaction{d.flags.missing_disclaimer_count !== 1 ? 's' : ''} missing disclaimer
            </div>
          )}
        </div>
      )}

      {/* Key metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard
          label="Total AI Interactions"
          value={d.total_interactions}
          sub={`Last ${d.period_days} days`}
        />
        <StatCard
          label="SEBI Compliance Rate"
          value={`${d.sebi_compliance_rate_pct}%`}
          sub="Target: ≥95%"
          color={complianceColor}
        />
        <StatCard
          label="Avg Confidence"
          value={d.average_confidence != null ? `${(d.average_confidence * 100).toFixed(0)}%` : '—'}
          sub="Target: ≥75%"
          color={confidenceColor}
        />
        <StatCard
          label="Disclaimer Injection"
          value={`${d.disclaimer_injection_rate_pct}%`}
          sub="SEBI mandatory"
          color={d.disclaimer_injection_rate_pct >= 99 ? 'text-green-600' : 'text-amber-600'}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Confidence distribution */}
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Confidence Distribution</h2>
          <div className="space-y-3">
            {[
              { key: 'high',    label: 'High (≥75%)',   color: 'bg-green-500' },
              { key: 'medium',  label: 'Medium (50–74%)', color: 'bg-amber-500' },
              { key: 'low',     label: 'Low (<50%)',    color: 'bg-red-500' },
              { key: 'unknown', label: 'Unknown',       color: 'bg-gray-300' },
            ].map(({ key, label, color }) => {
              const bucket = cd[key] || { count: 0, pct: 0 };
              return (
                <div key={key}>
                  <div className="flex justify-between text-xs text-gray-600 mb-1">
                    <span>{label}</span>
                    <span>{bucket.count} ({bucket.pct}%)</span>
                  </div>
                  <div className="w-full h-2 bg-gray-100 rounded-full">
                    <div
                      className={`h-full rounded-full ${color}`}
                      style={{ width: `${bucket.pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Tool usage */}
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Tool Usage</h2>
          {d.tool_usage?.length > 0 ? (
            <div className="space-y-2">
              {d.tool_usage.map((t) => (
                <div key={t.tool}>
                  <div className="flex justify-between text-xs text-gray-600 mb-1">
                    <span className="font-mono text-xs">{t.tool || 'general'}</span>
                    <span>{t.count} ({t.pct}%)</span>
                  </div>
                  <div className="w-full h-2 bg-gray-100 rounded-full">
                    <div
                      className="h-full rounded-full bg-blue-500"
                      style={{ width: `${t.pct}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400">No tool calls recorded.</p>
          )}
        </div>
      </div>

      {/* Daily trend */}
      {d.daily_trend?.length > 0 && (
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Daily Interactions (Last 7 Days)</h2>
          <div className="flex items-end gap-2 h-24">
            {(() => {
              const max = Math.max(...d.daily_trend.map(t => t.count), 1);
              return d.daily_trend.map((t) => (
                <div key={t.date} className="flex-1 flex flex-col items-center gap-1">
                  <span className="text-xs text-gray-500">{t.count}</span>
                  <div
                    className="w-full bg-blue-400 rounded-t"
                    style={{ height: `${(t.count / max) * 64}px`, minHeight: '4px' }}
                  />
                  <span className="text-xs text-gray-400 rotate-0" style={{ fontSize: '10px' }}>
                    {t.date.slice(5)}
                  </span>
                </div>
              ));
            })()}
          </div>
        </div>
      )}

      {/* Low confidence interactions */}
      {d.low_confidence_interactions?.length > 0 && (
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-700 mb-1">Low Confidence — Needs Review</h2>
          <p className="text-xs text-gray-400 mb-4">AI interactions below 50% confidence threshold</p>
          <div className="overflow-hidden rounded-lg border border-gray-100">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Client</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tool</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Query</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Confidence</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {d.low_confidence_interactions.map((l) => (
                  <tr key={l.log_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{l.client_name}</td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">{l.tool_name || '—'}</td>
                    <td className="px-4 py-3 text-gray-600 max-w-[240px] truncate">{l.query}</td>
                    <td className="px-4 py-3">
                      <ConfidenceBadge score={l.confidence_score} />
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-400">{formatDate(l.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function Header({ days, setDays }) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">AI Governance</h1>
        <p className="text-xs text-gray-500 mt-0.5">SEBI IA Regulations — AI model usage monitoring</p>
      </div>
      <select
        value={days}
        onChange={(e) => setDays(Number(e.target.value))}
        className="input-field text-sm"
      >
        <option value={7}>Last 7 days</option>
        <option value={30}>Last 30 days</option>
        <option value={90}>Last 90 days</option>
        <option value={365}>Last 365 days</option>
      </select>
    </div>
  );
}
