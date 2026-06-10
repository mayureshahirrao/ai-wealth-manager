import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth.js';
import ErrorBoundary from './components/ErrorBoundary.jsx';
import LoadingSpinner from './components/LoadingSpinner.jsx';
import LoginPage from './pages/Login.jsx';
import InvestorDashboard from './pages/investor/InvestorDashboard.jsx';
import RMDashboard from './pages/rm/RMDashboard.jsx';
import ComplianceDashboard from './pages/compliance/ComplianceDashboard.jsx';

function PrivateRoute({ children, allowedRoles }) {
  const { isAuthenticated, role, isLoading } = useAuth();

  if (isLoading) return <LoadingSpinner size="page" />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (allowedRoles && !allowedRoles.includes(role)) return <Navigate to="/login" replace />;

  return children;
}

function RoleRouter() {
  const { role, isAuthenticated } = useAuth();

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  switch (role) {
    case 'investor':   return <Navigate to="/investor" replace />;
    case 'rm':         return <Navigate to="/rm" replace />;
    case 'compliance': return <Navigate to="/compliance" replace />;
    default:           return <Navigate to="/login" replace />;
  }
}

export default function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <ErrorBoundary fullPage>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route
            path="/investor/*"
            element={
              <PrivateRoute allowedRoles={['investor']}>
                <ErrorBoundary fullPage>
                  <InvestorDashboard />
                </ErrorBoundary>
              </PrivateRoute>
            }
          />

          <Route
            path="/rm/*"
            element={
              <PrivateRoute allowedRoles={['rm']}>
                <ErrorBoundary fullPage>
                  <RMDashboard />
                </ErrorBoundary>
              </PrivateRoute>
            }
          />

          <Route
            path="/compliance/*"
            element={
              <PrivateRoute allowedRoles={['compliance']}>
                <ErrorBoundary fullPage>
                  <ComplianceDashboard />
                </ErrorBoundary>
              </PrivateRoute>
            }
          />

          <Route path="/" element={<RoleRouter />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </ErrorBoundary>
    </BrowserRouter>
  );
}
