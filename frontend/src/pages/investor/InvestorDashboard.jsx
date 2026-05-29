import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AppShell from '../../components/AppShell.jsx';
import PortfolioOverview from './PortfolioOverview.jsx';
import GoalsView from './GoalsView.jsx';
import ChatView from './ChatView.jsx';
import TaxView from './TaxView.jsx';

const NAV = [
  { to: '/investor/portfolio', label: 'Portfolio',   icon: '📊' },
  { to: '/investor/goals',     label: 'My Goals',    icon: '🎯' },
  { to: '/investor/chat',      label: 'AI Advisor',  icon: '💬' },
  { to: '/investor/tax',       label: 'Tax Planning', icon: '📋' },
];

export default function InvestorDashboard() {
  return (
    <AppShell navItems={NAV}>
      <Routes>
        <Route path="portfolio" element={<PortfolioOverview />} />
        <Route path="goals"     element={<GoalsView />} />
        <Route path="chat"      element={<ChatView />} />
        <Route path="tax"       element={<TaxView />} />
        <Route path="*"         element={<Navigate to="/investor/portfolio" replace />} />
      </Routes>
    </AppShell>
  );
}
