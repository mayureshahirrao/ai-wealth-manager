import React from 'react';
import { useAuth } from '../../hooks/useAuth.js';
import { useMyTaxSummary } from '../../hooks/useApi.js';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';

export default function TaxView() {
  const { data, isLoading } = useMyTaxSummary();

  if (isLoading) return <LoadingSpinner size="page" />;

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Tax Planning</h1>
      <div className="card">
        <p className="text-gray-500 text-sm">
          Tax analysis powered by AI — old vs new regime comparison, LTCG harvesting opportunities,
          and 80C optimization will be available in Phase 6.
        </p>
        {data?.data && (
          <pre className="mt-4 text-xs bg-gray-50 p-4 rounded-lg overflow-auto">
            {JSON.stringify(data.data, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
