import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useClients } from '../../hooks/useApi.js';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import INRAmount from '../../components/INRAmount.jsx';
import PercentBadge from '../../components/PercentBadge.jsx';
import { formatDaysAgo, formatXIRR } from '../../utils/formatters.js';
import { SEGMENT_COLORS } from '../../utils/constants.js';

export default function ClientList() {
  const { data, isLoading, error } = useClients();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');

  if (isLoading) return <LoadingSpinner size="page" label="Loading clients..." />;
  if (error)     return <div className="p-8 text-red-600">Failed to load clients.</div>;

  const clients = (data?.data || []).filter((c) =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Clients ({clients.length})</h1>
        <input
          type="text"
          placeholder="Search by name or email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input-field w-64"
        />
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Client</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Segment</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">AUM</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">XIRR</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Review</th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Alerts</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {clients.map((c) => (
              <tr
                key={c.client_id}
                onClick={() => navigate(`/rm/clients/${c.client_id}`)}
                className="hover:bg-blue-50 cursor-pointer transition-colors"
              >
                <td className="px-6 py-4">
                  <p className="font-medium text-gray-900">{c.name}</p>
                  <p className="text-xs text-gray-400">{c.email}</p>
                </td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${SEGMENT_COLORS[c.segment] || 'bg-gray-100 text-gray-700'}`}>
                    {c.segment?.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-6 py-4 text-right font-medium"><INRAmount value={c.total_aum} /></td>
                <td className="px-6 py-4 text-right">{formatXIRR(c.xirr)}</td>
                <td className="px-6 py-4 text-gray-500">{formatDaysAgo(c.days_since_review)}</td>
                <td className="px-6 py-4 text-center">
                  {c.has_active_alerts && (
                    <span className="inline-flex items-center justify-center w-5 h-5 bg-red-100 text-red-600 rounded-full text-xs">!</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
