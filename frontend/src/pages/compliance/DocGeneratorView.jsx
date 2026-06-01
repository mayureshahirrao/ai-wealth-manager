import React, { useState } from 'react';
import { useClients, useGenerateComplianceDoc } from '../../hooks/useApi.js';
import LoadingSpinner from '../../components/LoadingSpinner.jsx';

const DOC_TYPES = [
  { value: 'DISCLOSURE_DOC',        label: 'Disclosure Document',     desc: 'SEBI IA Reg. Clause 21 — adviser disclosure' },
  { value: 'RISK_PROFILE',          label: 'Risk Profile Assessment', desc: 'Client risk questionnaire and profile determination' },
  { value: 'SUITABILITY_ATTESTATION', label: 'Suitability Attestation', desc: 'SEBI Clause 19 — rationale for recommendations' },
  { value: 'KYC_RECORD',            label: 'KYC Record Summary',      desc: 'PMLA + SEBI KYC compliance record' },
  { value: 'MEETING_SUMMARY',       label: 'Meeting Summary',         desc: 'Post-meeting record with action items' },
];

export default function DocGeneratorView() {
  const [clientId, setClientId] = useState('');
  const [docType, setDocType] = useState('DISCLOSURE_DOC');
  const [context, setContext] = useState('');
  const [generatedDoc, setGeneratedDoc] = useState(null);

  const { data: clientsData } = useClients();
  const clients = clientsData?.data || [];

  const { mutate: generateDoc, isPending: generating } = useGenerateComplianceDoc();

  const selectedDocType = DOC_TYPES.find(d => d.value === docType);

  const handleGenerate = () => {
    if (!clientId || !docType) return;
    generateDoc(
      { client_id: clientId, doc_type: docType, context },
      {
        onSuccess: (data) => setGeneratedDoc(data.data),
        onError: (err) => alert(`Error: ${err.message}`),
      }
    );
  };

  const handleDownload = () => {
    if (!generatedDoc) return;
    const blob = new Blob([generatedDoc.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${docType.toLowerCase()}-${generatedDoc.client_name?.replace(/\s+/g, '-')}.txt`;
    a.click();
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">SEBI Document Generator</h1>
        <p className="text-xs text-gray-500 mt-0.5">
          AI-generated compliance documents — SEBI IA Regulations 2013
        </p>
      </div>

      {/* Config panel */}
      <div className="card space-y-4">
        <h2 className="text-sm font-semibold text-gray-700">Document Parameters</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Client */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Client</label>
            <select
              value={clientId}
              onChange={(e) => { setClientId(e.target.value); setGeneratedDoc(null); }}
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

          {/* Doc type */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Document Type</label>
            <select
              value={docType}
              onChange={(e) => { setDocType(e.target.value); setGeneratedDoc(null); }}
              className="input-field w-full"
            >
              {DOC_TYPES.map((d) => (
                <option key={d.value} value={d.value}>{d.label}</option>
              ))}
            </select>
            {selectedDocType && (
              <p className="text-xs text-gray-400 mt-1">{selectedDocType.desc}</p>
            )}
          </div>

          {/* Context / notes */}
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Additional Context (optional)
            </label>
            <textarea
              rows={2}
              placeholder="e.g. Meeting held on 01-Jun-2026, client interested in NPS top-up..."
              value={context}
              onChange={(e) => setContext(e.target.value)}
              className="input-field w-full resize-none"
            />
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleGenerate}
            disabled={!clientId || generating}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {generating ? (
              <span className="flex items-center gap-2">
                <LoadingSpinner size="sm" />
                Generating...
              </span>
            ) : '📄 Generate Document'}
          </button>
          {generating && (
            <p className="text-xs text-gray-500">Claude is drafting the document... (~15–30s)</p>
          )}
        </div>
      </div>

      {/* Generated document */}
      {generatedDoc && (
        <div className="card">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-gray-700">
                {selectedDocType?.label} — {generatedDoc.client_name}
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">
                Generated {new Date(generatedDoc.generated_at).toLocaleString()} · by {generatedDoc.generated_by}
              </p>
            </div>
            <div className="flex gap-2">
              <button onClick={handleDownload} className="btn-secondary text-xs">
                ⬇ Download
              </button>
              <button
                onClick={() => { setGeneratedDoc(null); }}
                className="btn-secondary text-xs"
              >
                ✕ Clear
              </button>
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
            <pre className="whitespace-pre-wrap font-sans text-sm text-gray-800 leading-relaxed">
              {generatedDoc.content}
            </pre>
          </div>

          <p className="text-xs text-gray-400 mt-3">
            Document ID: {generatedDoc.doc_id} · Saved to compliance audit trail.
          </p>
        </div>
      )}

      {!generatedDoc && !generating && (
        <div className="card text-center py-12">
          <p className="text-4xl mb-3">📋</p>
          <p className="text-gray-600 font-medium">No document generated yet</p>
          <p className="text-gray-400 text-sm mt-1">
            Select a client and document type, then click Generate.
          </p>
        </div>
      )}
    </div>
  );
}
