import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  useClientDetail, usePortfolio, useGoals,
  useClientAlerts, useGenerateMeetingPrep,
} from '../../hooks/useApi.js';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import INRAmount from '../../components/INRAmount.jsx';
import PercentBadge from '../../components/PercentBadge.jsx';
import { formatXIRR, formatDaysAgo } from '../../utils/formatters.js';

const TABS = ['Overview', 'Portfolio', 'Goals', 'Meeting Prep'];

export default function ClientDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('Overview');

  const { data: clientData, isLoading: loadingClient } = useClientDetail(id);
  const { data: portfolioData } = usePortfolio(id);
  const { data: goalsData } = useGoals(id);
  const { data: alertsData } = useClientAlerts(id);
  const {
    mutate: generateBrief,
    isPending: generatingBrief,
    data: briefData,
    error: briefError,
  } = useGenerateMeetingPrep(id);

  if (loadingClient) return <LoadingSpinner size="page" />;

  const client = clientData?.data;
  const portfolio = portfolioData?.data;
  const goals = goalsData?.data || [];
  const alerts = alertsData?.data || [];
  const brief = briefData?.data;

  if (!client) return <div className="p-8 text-gray-500">Client not found.</div>;

  return (
    <div className="p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/rm/clients')} className="text-blue-600 hover:underline text-sm">
          ← Clients
        </button>
        <h1 className="text-2xl font-bold text-gray-900">{client.name}</h1>
        <span className="text-sm text-gray-500 capitalize">
          {client.risk_profile} · {client.tax_regime?.toUpperCase()} Regime
        </span>
      </div>

      {/* Active alerts banner */}
      {alerts.length > 0 && (
        <div className="space-y-2">
          {alerts.map((a) => (
            <div key={a.alert_id} className={`px-4 py-3 rounded-lg border text-sm ${
              a.priority === 'high' || a.priority === 'critical'
                ? 'bg-red-50 border-red-200 text-red-800'
                : a.priority === 'medium'
                ? 'bg-amber-50 border-amber-200 text-amber-800'
                : 'bg-blue-50 border-blue-200 text-blue-800'
            }`}>
              <span className="font-bold uppercase text-xs">{a.priority}</span> — {a.message}
              {a.recommended_action && (
                <p className="text-xs mt-1 opacity-80 italic">→ {a.recommended_action}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Tab bar */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-6">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      {activeTab === 'Overview' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="card">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">Client Details</h2>
            <dl className="space-y-2 text-sm">
              <Row label="Email" value={client.email} />
              <Row label="Age" value={client.age} />
              <Row label="Annual Income" value={<INRAmount value={client.annual_income} />} />
              <Row label="KYC" value={client.kyc_verified ? '✓ Verified' : '⚠ Pending'} />
              <Row label="Tax Regime" value={client.tax_regime?.toUpperCase()} />
              <Row label="Risk Profile" value={<span className="capitalize">{client.risk_profile}</span>} />
            </dl>
          </div>
          {portfolio && (
            <div className="card">
              <h2 className="text-sm font-semibold text-gray-700 mb-3">Portfolio Snapshot</h2>
              <dl className="space-y-2 text-sm">
                <Row label="AUM" value={<INRAmount value={portfolio.current_value} />} />
                <Row label="Invested" value={<INRAmount value={portfolio.total_invested} />} />
                <Row label="XIRR" value={<span className="text-blue-600 font-semibold">{formatXIRR(portfolio.xirr)}</span>} />
                <Row label="Benchmark" value={formatXIRR(portfolio.benchmark_xirr)} />
                <Row label="Active Alerts" value={alerts.length || 0} />
              </dl>
            </div>
          )}
        </div>
      )}

      {activeTab === 'Portfolio' && (
        <div className="space-y-4">
          {portfolio ? (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { label: 'Current Value', val: <INRAmount value={portfolio.current_value} /> },
                  { label: 'XIRR', val: <span className="text-blue-600 font-semibold">{formatXIRR(portfolio.xirr)}</span> },
                  { label: 'Benchmark XIRR', val: formatXIRR(portfolio.benchmark_xirr) },
                  { label: 'Holdings', val: portfolio.holdings?.length || 0 },
                ].map(({ label, val }) => (
                  <div key={label} className="card text-center">
                    <p className="text-xs text-gray-500">{label}</p>
                    <p className="font-semibold text-gray-900 mt-1">{val}</p>
                  </div>
                ))}
              </div>
              {portfolio.holdings?.length > 0 && (
                <div className="card p-0 overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs text-gray-500 uppercase">Scheme</th>
                        <th className="px-4 py-3 text-left text-xs text-gray-500 uppercase">Class</th>
                        <th className="px-4 py-3 text-right text-xs text-gray-500 uppercase">Value</th>
                        <th className="px-4 py-3 text-right text-xs text-gray-500 uppercase">Gain/Loss</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {portfolio.holdings.map((h, i) => {
                        const gain = h.current_value - h.invested_amount;
                        const pct = h.invested_amount > 0 ? gain / h.invested_amount * 100 : 0;
                        return (
                          <tr key={i}>
                            <td className="px-4 py-3 font-medium text-gray-900 max-w-[200px] truncate">{h.scheme_name}</td>
                            <td className="px-4 py-3 text-gray-500 capitalize">{h.asset_class}</td>
                            <td className="px-4 py-3 text-right"><INRAmount value={h.current_value} /></td>
                            <td className={`px-4 py-3 text-right font-medium ${gain >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {pct >= 0 ? '+' : ''}{pct.toFixed(1)}%
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          ) : (
            <div className="card text-center py-8 text-gray-400">No portfolio data available.</div>
          )}
        </div>
      )}

      {activeTab === 'Goals' && (
        <div className="space-y-3">
          {goals.length === 0 ? (
            <div className="card text-center py-8 text-gray-400">No goals configured for this client.</div>
          ) : (
            goals.map((g) => (
              <div key={g.goal_id} className="card">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">{g.goal_name}</h3>
                    <p className="text-xs text-gray-500 capitalize">{g.goal_type?.replace('_', ' ')} · Target year {g.target_year}</p>
                  </div>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                    g.progress_pct >= 90 ? 'bg-green-100 text-green-700' :
                    g.progress_pct >= 70 ? 'bg-blue-100 text-blue-700' :
                    g.progress_pct >= 40 ? 'bg-amber-100 text-amber-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {g.progress_pct?.toFixed(0)}% feasible
                  </span>
                </div>
                <div className="mt-3 w-full h-2 bg-gray-100 rounded-full">
                  <div
                    className={`h-full rounded-full ${
                      g.progress_pct >= 90 ? 'bg-green-500' :
                      g.progress_pct >= 70 ? 'bg-blue-500' :
                      g.progress_pct >= 40 ? 'bg-amber-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${Math.min(g.progress_pct, 100)}%` }}
                  />
                </div>
                <div className="grid grid-cols-3 gap-2 mt-3 text-xs text-gray-500">
                  <div><span className="block font-medium text-gray-700"><INRAmount value={g.target_amount} /></span>Target</div>
                  <div><span className="block font-medium text-gray-700"><INRAmount value={g.current_corpus} /></span>Corpus</div>
                  <div><span className="block font-medium text-gray-700">₹{(g.monthly_sip / 1000).toFixed(0)}K/mo</span>SIP</div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'Meeting Prep' && (
        <div className="space-y-4">
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-gray-700">AI Meeting Brief</h2>
                <p className="text-xs text-gray-500 mt-0.5">
                  Claude generates a structured meeting agenda based on live portfolio and goal data.
                </p>
              </div>
              <button
                onClick={() => generateBrief()}
                disabled={generatingBrief}
                className="btn-primary text-sm disabled:opacity-50"
              >
                {generatingBrief ? (
                  <span className="flex items-center gap-2">
                    <LoadingSpinner size="sm" /> Generating...
                  </span>
                ) : brief ? '↻ Regenerate Brief' : '✨ Generate Meeting Brief'}
              </button>
            </div>
          </div>

          {generatingBrief && (
            <div className="card text-center py-10">
              <LoadingSpinner size="md" label="Claude is preparing your meeting brief..." />
            </div>
          )}

          {brief && !generatingBrief && (
            <div className="card">
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs text-gray-500">
                  Generated {new Date(brief.generated_at).toLocaleString()}
                </p>
                <div className="flex gap-2 text-xs text-gray-500">
                  <span>AUM: <INRAmount value={brief.context_summary?.aum} /></span>
                  <span>·</span>
                  <span>Alerts: {brief.context_summary?.active_alerts}</span>
                  <span>·</span>
                  <span>Goals: {brief.context_summary?.goals_count}</span>
                </div>
              </div>
              <pre className="whitespace-pre-wrap font-sans text-sm text-gray-800 leading-relaxed">
                {brief.brief}
              </pre>
            </div>
          )}

          {briefError && !generatingBrief && (
            <div className="card border border-red-200 bg-red-50 text-red-700 p-4 text-sm">
              <p className="font-semibold">Failed to generate brief</p>
              <p className="mt-1 text-xs">{briefError.message}</p>
            </div>
          )}

          {!brief && !generatingBrief && !briefError && (
            <div className="card text-center py-12">
              <p className="text-4xl mb-3">🤝</p>
              <p className="text-gray-600 font-medium">No brief generated yet</p>
              <p className="text-gray-400 text-sm mt-1">
                Click "Generate Meeting Brief" for an AI-powered meeting agenda.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between items-start gap-2">
      <dt className="text-gray-500 shrink-0">{label}</dt>
      <dd className="font-medium text-gray-900 text-right">{value}</dd>
    </div>
  );
}
