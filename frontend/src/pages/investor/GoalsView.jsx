import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useMyGoals } from '../../hooks/useApi.js';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';
import INRAmount from '../../components/INRAmount.jsx';
import { goalsToBarData } from '../../utils/chartHelpers.js';
import { formatFeasibilityScore } from '../../utils/formatters.js';
import { GOAL_ICONS } from '../../utils/constants.js';

export default function GoalsView() {
  const { data, isLoading, error } = useMyGoals();

  if (isLoading) return <LoadingSpinner size="page" label="Loading goals..." />;
  if (error)     return <div className="p-8 text-red-600">Failed to load goals.</div>;

  const goals = data?.data || [];
  const barData = goalsToBarData(goals);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">My Financial Goals</h1>

      {goals.length === 0 && (
        <div className="card text-center py-12">
          <p className="text-gray-400">No goals set yet. Talk to your advisor to create a plan.</p>
        </div>
      )}

      {/* Goal Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {goals.map((goal) => {
          const feasibility = formatFeasibilityScore(goal.feasibility_score || 50);
          const icon = GOAL_ICONS[goal.goal_type] || '🎯';
          const progressPct = Math.min(goal.progress_pct || 0, 100);

          return (
            <div key={goal.goal_id} className="card">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{icon}</span>
                  <div>
                    <p className="font-semibold text-gray-900">{goal.goal_name}</p>
                    <p className="text-xs text-gray-500 capitalize">{goal.goal_type.replace('_', ' ')} · Target: {goal.target_year}</p>
                  </div>
                </div>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${feasibility.bg} ${feasibility.color}`}>
                  {feasibility.label}
                </span>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Current</span>
                  <INRAmount value={goal.current_corpus} className="font-medium" />
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Target</span>
                  <INRAmount value={goal.target_amount} className="font-medium" />
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Monthly SIP</span>
                  <INRAmount value={goal.monthly_sip} className="font-medium text-blue-600" />
                </div>
              </div>

              {/* Progress bar */}
              <div className="mt-3">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>Progress</span>
                  <span>{progressPct.toFixed(1)}%</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full transition-all"
                    style={{ width: `${progressPct}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Bar Chart */}
      {barData.length > 0 && (
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Goals Progress (₹ in Lakhs)</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={barData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => `₹${v}L`} />
              <YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => `₹${v}L`} />
              <Bar dataKey="current" name="Current" fill="#3b82f6" radius={[0, 4, 4, 0]} />
              <Bar dataKey="target" name="Target" fill="#e5e7eb" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
