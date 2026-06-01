import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useClients, useFinancialPlan, useGenerateFinancialPlan } from '../../hooks/useApi.js';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';

export default function FinancialPlanView() {
  const { id: clientIdFromParams } = useParams();
  const navigate = useNavigate();

  const [selectedClientId, setSelectedClientId] = useState(clientIdFromParams || '');
  const [desiredIncome, setDesiredIncome] = useState(100000);
  const [retirementAge, setRetirementAge] = useState(60);
  const [advisorNotes, setAdvisorNotes] = useState('');

  const { data: clientsData } = useClients();
  const clients = clientsData?.data || [];

  const { data: planData, isLoading: loadingPlan } = useFinancialPlan(selectedClientId);
  const { mutate: generatePlan, isPending: generating } = useGenerateFinancialPlan();

  const existingPlan = planData?.data;
  const [generatedPlan, setGeneratedPlan] = useState(null);
  const displayPlan = generatedPlan || (existingPlan?.plan ? existingPlan : null);

  const handleGenerate = () => {
    if (!selectedClientId) return;
    generatePlan(
      {
        client_id: selectedClientId,
        advisor_notes: advisorNotes,
        target_retirement_age: retirementAge,
        desired_monthly_income: desiredIncome,
      },
      {
        onSuccess: (data) => setGeneratedPlan(data.data),
        onError: (err) => alert(`Error: ${err.message}`),
      }
    );
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Financial Plan Generator</h1>
      </div>

      {/* Config panel */}
      <div className="card space-y-4">
        <h2 className="text-sm font-semibold text-gray-700">Plan Parameters</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Client selector */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Client</label>
            <select
              value={selectedClientId}
              onChange={(e) => { setSelectedClientId(e.target.value); setGeneratedPlan(null); }}
              className="input-field w-full"
            >
              <option value="">Select a client...</option>
              {clients.map((c) => (
                <option key={c.client_id} value={c.client_id}>
                  {c.name} — {c.email}
                </option>
              ))}
            </select>
          </div>

          {/* Retirement age */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Target Retirement Age
            </label>
            <input
              type="number"
              min={50} max={80}
              value={retirementAge}
              onChange={(e) => setRetirementAge(Number(e.target.value))}
              className="input-field w-full"
            />
          </div>

          {/* Desired income */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Desired Monthly Income at Retirement (today's ₹)
            </label>
            <input
              type="number"
              min={10000} step={5000}
              value={desiredIncome}
              onChange={(e) => setDesiredIncome(Number(e.target.value))}
              className="input-field w-full"
            />
            <p className="text-xs text-gray-400 mt-1">
              ₹{(desiredIncome / 100000).toFixed(1)}L/month
            </p>
          </div>

          {/* Advisor notes */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              RM Notes (optional)
            </label>
            <textarea
              rows={2}
              placeholder="e.g. Client planning to start a business in 3 years..."
              value={advisorNotes}
              onChange={(e) => setAdvisorNotes(e.target.value)}
              className="input-field w-full resize-none"
            />
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleGenerate}
            disabled={!selectedClientId || generating}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {generating ? (
              <span className="flex items-center gap-2">
                <LoadingSpinner size="sm" />
                Generating Plan...
              </span>
            ) : '✨ Generate Financial Plan'}
          </button>
          {generating && (
            <p className="text-xs text-gray-500">
              Claude is analysing the client's full financial picture... (~30–60s)
            </p>
          )}
        </div>
      </div>

      {/* Plan display */}
      {loadingPlan && selectedClientId && (
        <div className="card text-center py-8">
          <LoadingSpinner size="md" label="Loading saved plan..." />
        </div>
      )}

      {displayPlan && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-gray-700">
                Financial Plan — {displayPlan.client_name || 'Client'}
              </h2>
              {displayPlan.generated_at && (
                <p className="text-xs text-gray-400 mt-0.5">
                  Generated {new Date(displayPlan.generated_at).toLocaleString()} by {displayPlan.generated_by}
                </p>
              )}
            </div>
            <button
              onClick={() => {
                const blob = new Blob([displayPlan.plan || ''], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `financial-plan-${selectedClientId}.txt`;
                a.click();
              }}
              className="btn-secondary text-xs"
            >
              ⬇ Download
            </button>
          </div>

          {/* Render plan as formatted text */}
          <div className="prose prose-sm max-w-none">
            <pre className="whitespace-pre-wrap font-sans text-sm text-gray-800 leading-relaxed">
              {displayPlan.plan}
            </pre>
          </div>

          {displayPlan.tokens_used && (
            <p className="text-xs text-gray-400 mt-4 text-right">
              {displayPlan.tokens_used} tokens used
            </p>
          )}
        </div>
      )}

      {!displayPlan && selectedClientId && !loadingPlan && !generating && (
        <div className="card text-center py-12">
          <p className="text-4xl mb-3">📄</p>
          <p className="text-gray-600 font-medium">No plan generated yet</p>
          <p className="text-gray-400 text-sm mt-1">
            Click "Generate Financial Plan" to create one for this client.
          </p>
        </div>
      )}
    </div>
  );
}
