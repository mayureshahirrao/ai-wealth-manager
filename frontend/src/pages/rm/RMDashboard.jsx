import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AppShell from '../../components/AppShell.jsx';
import ClientList from './ClientList.jsx';
import ClientDetail from './ClientDetail.jsx';
import NextActions from './NextActions.jsx';
import FinancialPlanView from './FinancialPlanView.jsx';

const NAV = [
  { to: '/rm/clients',      label: 'Clients',          icon: '👥' },
  { to: '/rm/next-actions', label: 'Next Best Actions', icon: '⚡' },
  { to: '/rm/plans',        label: 'Financial Plans',   icon: '📄' },
];

export default function RMDashboard() {
  return (
    <AppShell navItems={NAV}>
      <Routes>
        <Route path="clients"          element={<ClientList />} />
        <Route path="clients/:id"      element={<ClientDetail />} />
        <Route path="next-actions"     element={<NextActions />} />
        <Route path="plans"            element={<FinancialPlanView />} />
        <Route path="*"                element={<Navigate to="/rm/clients" replace />} />
      </Routes>
    </AppShell>
  );
}
