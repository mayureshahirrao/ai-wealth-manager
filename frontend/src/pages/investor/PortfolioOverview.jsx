import React from 'react';
import { PieChart, Pie, Cell, Tooltip, LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from 'recharts';
import { useMyPortfolio, useNAVHistory } from '../../hooks/useApi.js';
import { useAuth } from '../../hooks/useAuth.js';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import INRAmount from '../../components/INRAmount.jsx';
import PercentBadge from '../../components/PercentBadge.jsx';
import { holdingsToPieData, navHistoryToLineData } from '../../utils/chartHelpers.js';
import { formatXIRR, formatPnLPercent } from '../../utils/formatters.js';
import { ASSET_CLASS_COLORS } from '../../utils/constants.js';

export default function PortfolioOverview() {
  const { clientId } = useAuth();
  const { data: portfolio, isLoading, error } = useMyPortfolio();
  const { data: navData } = useNAVHistory(clientId);

  if (isLoading) return <LoadingSpinner size="page" label="Loading portfolio..." />;
  if (error)     return <div className="p-8 text-red-600">Failed to load portfolio: {error.message}</div>;
  if (!portfolio?.data) return null;

  const p = portfolio.data;
  const pnl = p.current_value - p.total_invested;
  const pnlPct = p.total_invested > 0 ? pnl / p.total_invested : 0;
  const pieData = holdingsToPieData(p.holdings || []);
  const lineData = navData?.data ? navHistoryToLineData(navData.data) : [];

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Portfolio Overview</h1>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Current Value" value={<INRAmount value={p.current_value} />} />
        <StatCard label="Total Invested" value={<INRAmount value={p.total_invested} />} />
        <StatCard
          label="Total P&L"
          value={<span className={pnl >= 0 ? 'text-green-600' : 'text-red-600'}><INRAmount value={pnl} /></span>}
          sub={<PercentBadge value={pnlPct} />}
        />
        <StatCard label="XIRR" value={<span className="text-blue-600">{formatXIRR(p.xirr)}</span>}
          sub={<span className="text-xs text-gray-500">Benchmark: {formatXIRR(p.benchmark_xirr)}</span>}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Allocation Pie */}
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Asset Allocation</h2>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({name, pct}) => `${name} ${pct}%`}>
                  {pieData.map((entry) => (
                    <Cell key={entry.assetClass} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip formatter={(v) => [`₹${(v/100000).toFixed(1)}L`, 'Value']} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-sm text-center py-8">No holdings data</p>
          )}
        </div>

        {/* NAV History Line */}
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Portfolio vs Benchmark</h2>
          {lineData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={lineData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => `₹${(v/100000).toFixed(0)}L`} />
                <Tooltip formatter={(v) => `₹${(v/100000).toFixed(1)}L`} />
                <Line type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={2} dot={false} name="Portfolio" />
                <Line type="monotone" dataKey="benchmark" stroke="#9ca3af" strokeWidth={2} dot={false} name="Benchmark" strokeDasharray="4 4" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-sm text-center py-8">No history data</p>
          )}
        </div>
      </div>

      {/* Holdings Table */}
      <div className="card">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Holdings</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b border-gray-200">
                <th className="pb-2 font-medium text-gray-500">Scheme</th>
                <th className="pb-2 font-medium text-gray-500 text-right">Invested</th>
                <th className="pb-2 font-medium text-gray-500 text-right">Current</th>
                <th className="pb-2 font-medium text-gray-500 text-right">P&L</th>
                <th className="pb-2 font-medium text-gray-500">Type</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {(p.holdings || []).map((h, i) => {
                const hPnL = h.current_value - h.invested_amount;
                const hPnLPct = h.invested_amount > 0 ? hPnL / h.invested_amount : 0;
                return (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="py-2.5 pr-4">
                      <p className="font-medium text-gray-900 truncate max-w-[200px]">{h.scheme_name}</p>
                      {h.has_sip_active && <span className="text-xs text-blue-600">SIP Active</span>}
                    </td>
                    <td className="py-2.5 text-right text-gray-600"><INRAmount value={h.invested_amount} /></td>
                    <td className="py-2.5 text-right font-medium"><INRAmount value={h.current_value} /></td>
                    <td className="py-2.5 text-right"><PercentBadge value={hPnLPct} /></td>
                    <td className="py-2.5">
                      <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 capitalize">
                        {h.asset_class}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, sub }) {
  return (
    <div className="card">
      <p className="stat-label">{label}</p>
      <p className="stat-value text-xl">{value}</p>
      {sub && <div className="mt-1">{sub}</div>}
    </div>
  );
}
