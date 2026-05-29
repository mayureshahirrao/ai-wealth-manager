/**
 * AppShell.jsx — Top navigation + sidebar layout wrapper.
 * Used by all three role dashboards.
 */

import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth.js';

export default function AppShell({ navItems, children }) {
  const { user, role, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  function handleLogout() {
    logout();
    navigate('/login');
  }

  const roleColors = {
    investor:   'bg-blue-600',
    rm:         'bg-indigo-600',
    compliance: 'bg-purple-600',
  };
  const sidebarColor = roleColors[role] || 'bg-blue-600';

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <aside className={`w-64 flex-shrink-0 flex flex-col ${sidebarColor} text-white`}>
        {/* Brand */}
        <div className="flex items-center gap-2 px-6 py-5 border-b border-white/20">
          <span className="text-xl font-bold">WealthMind AI</span>
        </div>

        {/* User info */}
        <div className="px-6 py-4 border-b border-white/20">
          <p className="text-sm font-medium truncate">{user?.name || user?.email}</p>
          <p className="text-xs text-white/60 capitalize mt-0.5">{role}</p>
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-white/20 text-white'
                    : 'text-white/70 hover:bg-white/10 hover:text-white'
                }`
              }
            >
              {item.icon && <span className="text-lg">{item.icon}</span>}
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Logout */}
        <div className="px-3 py-4 border-t border-white/20">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-white/70 hover:bg-white/10 hover:text-white transition-colors"
          >
            <span>→</span>
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto">
          {children}
        </div>
      </main>
    </div>
  );
}
