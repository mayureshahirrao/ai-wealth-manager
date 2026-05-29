import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useClientDetail, usePortfolio, useGoals, useClientAlerts } from '../../hooks/useApi.js';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import INRAmount from '../../components/INRAmount.jsx';
import PercentBadge from '../../components/PercentBadge.jsx';
import { formatXIRR, formatDaysAgo } from '../../utils/formatters.js';

export default function ClientDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: clientData, isLoading: loadingClient } = useClientDetail(id);
  const { data: portfolioData } = usePortfolio(id);
  const { data: goalsData } = useGoals(id);
  const { data: alertsData } = useClientAlerts(id);

  if (loadingClient) return <LoadingSpinner size="page" />;

  const client = clientData?.data;
  const portfolio = portfolioData?.data;
  const goals = goalsData?.data || [];
  const alerts = alertsData?.data || [];

  if (!client) return <div className="p-8 text-gray-500">Client not found.</div>;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/rm/clients')} className="text-blue-600 hover:underline text-sm">
          ← Clients
        </button>
        <h1 className="text-2xl font-bold text-gray-900">{client.name}</h1>
        <span className="text-sm text-gray-500 capitalize">{client.risk_profile} · {client.tax_regime} Regime</span>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="space-y-2">
          {alerts.map((a) => (
            <div key={a.alert_id} className={`px-4 py-3 rounded-lg border text-sm ${
              a.priority === 'high' ? 'bg-red-50 border-red-200 text-red-800' :
              a.priority === 'medium' ? 'bg-amber-50 border-amber-200 text-amber-800' :
              'bg-blue-50 border-blue-200 text-blue-800'
            }`}>
              <span className="font-medium uppercase text-xs">{a.priority}</span> — {a.message}
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Portfolio Summary */}
        {portfolio && (
          <div className="card">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">Portfolio</h2>
            <dl className="space-y-2 text-sm">
              <Row label="Current Value" value={<INRAmount value={portfolio.current_value} />} />
              <Row label="Total Invested" value={<INRAmount value={portfolio.total_invested} />} />
              <Row label="XIRR" value={<span className="text-blue-600 font-medium">{formatXIRR(portfolio.xirr)}</span>} />
              <Row label="Benchmark XIRR" value={formatXIRR(portfolio.benchmark_xirr)} />
              <Row label="Holdings" value={portfolio.holdings?.length || 0} />
            </dl>
          </div>
        )}

        {/* Goals Summary */}
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Goals ({goals.length})</h2>
          <div className="space-y-2">
            {goals.slice(0, 3).map((g) => (
              <div key={g.goal_id} className="flex items-center justify-between text-sm">
                <span className="text-gray-700 truncate max-w-[150px]">{g.goal_name}</span>
                <div className="flex items-center gap-2">
                  <span className="text-gray-500">{g.progress_pct?.toFixed(1)}%</span>
                  <div className="w-16 h-1.5 bg-gray-100 rounded-full">
                    <div className="h-full bg-blue-500 rounded-full" style={{ width: `${Math.min(g.progress_pct, 100)}%` }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Client Info */}
      <div className="card">
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Client Details</h2>
        <dl className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <Row label="Email" value={client.email} />
          <Row label="Age" value={client.age} />
          <Row label="Annual Income" value={<INRAmount value={client.annual_income} />} />
          <Row label="KYC" value={client.kyc_verified ? 'Verified' : 'Pending'} />
          <Row label="Tax Regime" value={client.tax_regime?.toUpperCase()} />
          <Row label="Risk Profile" value={client.risk_profile} />
        </dl>
      </div>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between">
      <dt className="text-gray-500">{label}</dt>
      <dd className="font-medium text-gray-900">{value}</dd>
    </div>
  );
}
