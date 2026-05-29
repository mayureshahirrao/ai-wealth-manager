import React from 'react';
import { useNextActions } from '../../hooks/useApi.js';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';

export default function NextActions() {
  const { data, isLoading } = useNextActions();

  if (isLoading) return <LoadingSpinner size="page" />;

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">Next Best Actions</h1>
      <div className="card">
        <p className="text-gray-500 text-sm">
          AI-powered next best actions for your clients — coming in Phase 7.
        </p>
        {data?.data?.actions?.length === 0 && (
          <p className="text-gray-400 text-sm mt-4">No pending actions.</p>
        )}
      </div>
    </div>
  );
}
