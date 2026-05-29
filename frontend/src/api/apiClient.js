/**
 * apiClient.js — Configured Axios instance with JWT and error handling.
 *
 * All API calls must use this client. Never call axios.get/post directly.
 * Provides:
 * - Automatic JWT injection from localStorage
 * - 401 → auto logout + redirect to login
 * - Consistent error shape extraction
 *
 * Dependencies: endpoints.js, constants.js (Tier 2)
 * Consumed by: All service functions and useApi hook
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const TOKEN_KEY = 'wealth_manager_token';
const ROLE_KEY  = 'wealth_manager_role';
const USER_KEY  = 'wealth_manager_user';

// ─── Axios Instance ───────────────────────────────────────────────────────────

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30_000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// ─── Request Interceptor: Inject JWT ─────────────────────────────────────────

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// ─── Response Interceptor: Handle Errors ─────────────────────────────────────

apiClient.interceptors.response.use(
  (response) => response.data,   // Unwrap: return response.data directly
  (error) => {
    if (error.response?.status === 401) {
      // Clear auth state and redirect to login
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(ROLE_KEY);
      localStorage.removeItem(USER_KEY);
      window.location.href = '/login';
      return Promise.reject(new Error('Session expired. Please log in again.'));
    }

    // Extract error message from our standard APIResponse shape
    const apiError = error.response?.data;
    const message = apiError?.message || error.message || 'An unexpected error occurred';
    const errorCode = apiError?.error_code || 'UNKNOWN_ERROR';

    const enrichedError = new Error(message);
    enrichedError.errorCode = errorCode;
    enrichedError.status = error.response?.status;
    enrichedError.details = apiError?.details;

    return Promise.reject(enrichedError);
  },
);

// ─── Auth Helpers ─────────────────────────────────────────────────────────────

export const authStorage = {
  setToken: (token) => localStorage.setItem(TOKEN_KEY, token),
  getToken: () => localStorage.getItem(TOKEN_KEY),
  removeToken: () => localStorage.removeItem(TOKEN_KEY),
  setRole: (role) => localStorage.setItem(ROLE_KEY, role),
  getRole: () => localStorage.getItem(ROLE_KEY),
  setUser: (user) => localStorage.setItem(USER_KEY, JSON.stringify(user)),
  getUser: () => {
    try { return JSON.parse(localStorage.getItem(USER_KEY)); }
    catch { return null; }
  },
  clearAll: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(ROLE_KEY);
    localStorage.removeItem(USER_KEY);
  },
};

export { API_BASE_URL };
export default apiClient;
