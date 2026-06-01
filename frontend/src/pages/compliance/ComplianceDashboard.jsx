import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AppShell from '../../components/AppShell.jsx';
import AuditLogView from './AuditLogView.jsx';
import RiskAlertsView from './RiskAlertsView.jsx';
import AIGovernanceView from './AIGovernanceView.jsx';
import DocGeneratorView from './DocGeneratorView.jsx';

const NAV = [
  { to: '/compliance/audit-log',    label: 'Audit Log',      icon: '📝' },
  { to: '/compliance/risk-alerts',  label: 'Risk Alerts',    icon: '⚠' },
  { to: '/compliance/ai-governance', label: 'AI Governance', icon: '🤖' },
  { to: '/compliance/doc-generator', label: 'Doc Generator', icon: '📋' },
];

export default function ComplianceDashboard() {
  return (
    <AppShell navItems={NAV}>
      <Routes>
        <Route path="audit-log"     element={<AuditLogView />} />
        <Route path="risk-alerts"   element={<RiskAlertsView />} />
        <Route path="ai-governance" element={<AIGovernanceView />} />
        <Route path="doc-generator" element={<DocGeneratorView />} />
        <Route path="*"             element={<Navigate to="/compliance/audit-log" replace />} />
      </Routes>
    </AppShell>
  );
}
