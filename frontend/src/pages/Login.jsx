import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth.js';
import { DEMO_INVESTORS, DEMO_PASSWORD } from '../utils/constants.js';

const DEMO_LOGINS = [
  { label: 'Investor (Priya Sharma)', email: 'priya.sharma@demo.com',    role: 'investor' },
  { label: 'RM (Rahul Mehta)',        email: 'rm@wealthmanager.com',      role: 'rm' },
  { label: 'Compliance (Anita)',      email: 'compliance@wealthmanager.com', role: 'compliance' },
];

export default function LoginPage() {
  const { login, isAuthenticated, isLoading, error, role } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [localError, setLocalError] = useState('');

  useEffect(() => {
    if (isAuthenticated && role) {
      navigate(role === 'investor' ? '/investor' : role === 'rm' ? '/rm' : '/compliance', { replace: true });
    }
  }, [isAuthenticated, role, navigate]);

  async function handleSubmit(e) {
    e.preventDefault();
    setLocalError('');
    const result = await login(email, password);
    if (!result.success) {
      setLocalError(result.error || 'Login failed');
    }
  }

  function fillDemo(demoEmail) {
    setEmail(demoEmail);
    setPassword(DEMO_PASSWORD);
    setLocalError('');
  }

  const displayError = localError || error;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo / Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white/10 rounded-2xl mb-4">
            <span className="text-3xl">W</span>
          </div>
          <h1 className="text-3xl font-bold text-white">WealthMind AI</h1>
          <p className="text-blue-200 mt-1">AI-Powered Wealth Management</p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Sign in to your account</h2>

          {displayError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {displayError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-field"
                placeholder="you@example.com"
                required
                autoComplete="email"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field"
                placeholder="••••••••"
                required
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full py-2.5 mt-2"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          {/* Demo Quick-Fill */}
          <div className="mt-6 pt-5 border-t border-gray-100">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">
              Demo accounts (password: {DEMO_PASSWORD})
            </p>
            <div className="space-y-2">
              {DEMO_LOGINS.map((d) => (
                <button
                  key={d.email}
                  onClick={() => fillDemo(d.email)}
                  className="w-full text-left px-3 py-2 rounded-lg border border-gray-200 hover:bg-blue-50 hover:border-blue-300 transition-colors"
                >
                  <span className="text-sm font-medium text-gray-800">{d.label}</span>
                  <span className="block text-xs text-gray-400">{d.email}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <p className="text-center text-blue-300 text-xs mt-6">
          SEBI Registered Investment Adviser · Demo Environment
        </p>
      </div>
    </div>
  );
}
