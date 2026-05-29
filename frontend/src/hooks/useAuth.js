/**
 * useAuth.js — Authentication context hook.
 *
 * Provides:
 * - Current user object and role
 * - login() / logout() actions
 * - Role-check helpers (isInvestor, isRM, isCompliance)
 *
 * Dependencies: apiClient.js (Tier 2)
 * Consumed by: All components that need auth state, PrivateRoute, role guards
 *
 * Setup: Wrap app in <AuthProvider> in App.jsx
 */

import React, { createContext, useContext, useState, useCallback } from 'react';
import apiClient, { authStorage } from '../api/apiClient.js';
import { ENDPOINTS } from '../api/endpoints.js';
import { ROLES } from '../utils/constants.js';

// ─── Context ──────────────────────────────────────────────────────────────────

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => authStorage.getUser());
  const [role, setRole] = useState(() => authStorage.getRole());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const login = useCallback(async (email, password) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.post(ENDPOINTS.AUTH.LOGIN, { email, password });
      const { access_token, role: userRole, user_name, client_id } = response.data;

      authStorage.setToken(access_token);
      authStorage.setRole(userRole);
      authStorage.setUser({ name: user_name, email, role: userRole, clientId: client_id });

      setUser({ name: user_name, email, role: userRole, clientId: client_id });
      setRole(userRole);

      return { success: true, role: userRole };
    } catch (err) {
      const message = err.message || 'Login failed';
      setError(message);
      return { success: false, error: message };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    authStorage.clearAll();
    setUser(null);
    setRole(null);
  }, []);

  const value = {
    user,
    role,
    isLoading,
    error,
    login,
    logout,
    isAuthenticated: !!user,
    isInvestor:  role === ROLES.INVESTOR,
    isRM:        role === ROLES.RM,
    isCompliance: role === ROLES.COMPLIANCE,
    clientId: user?.clientId,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

/**
 * useAuth hook — access auth state and actions.
 *
 * @example
 * const { user, isInvestor, login, logout } = useAuth();
 * if (!isInvestor) return <Navigate to="/login" />;
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an <AuthProvider>');
  }
  return context;
}
