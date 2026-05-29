/**
 * endpoints.js — All API endpoint URL constants.
 *
 * Never hardcode URLs in components or hooks.
 * Import from here to catch typos and make refactoring painless.
 *
 * Dependencies: constants.js (Tier 1)
 * Consumed by: useApi hook, service functions
 */

export const ENDPOINTS = {
  // ── Auth ──────────────────────────────────────────────────────────────────
  AUTH: {
    LOGIN: '/api/auth/login',
    ME:    '/api/auth/me',
  },

  // ── Client / Investor ─────────────────────────────────────────────────────
  CLIENTS: {
    LIST:              '/api/clients',
    DETAIL:            (id) => `/api/clients/${id}`,
    PORTFOLIO:         (id) => `/api/clients/${id}/portfolio`,
    GOALS:             (id) => `/api/clients/${id}/goals`,
    TAX_SUMMARY:       (id) => `/api/clients/${id}/tax-summary`,
    NAV_HISTORY:       (id) => `/api/clients/${id}/nav-history`,
    PERFORMANCE:       (id) => `/api/clients/${id}/performance`,
  },

  // ── Chat / AI ─────────────────────────────────────────────────────────────
  CHAT: {
    MESSAGE:          '/api/chat/message',          // POST — returns SSE stream
    HISTORY:          (clientId) => `/api/chat/history/${clientId}`,
  },

  // ── Relationship Manager (RM) ─────────────────────────────────────────────
  RM: {
    NEXT_ACTIONS:     '/api/rm/next-actions',
    MEETING_PREP:     (clientId) => `/api/rm/meeting-prep/${clientId}`,
    CLIENT_ALERTS:    (clientId) => `/api/rm/alerts/${clientId}`,
  },

  // ── Financial Plan ─────────────────────────────────────────────────────────
  FINANCIAL_PLAN: {
    GENERATE:         '/api/financial-plan/generate',
    GET:              (clientId) => `/api/financial-plan/${clientId}`,
  },

  // ── Compliance ────────────────────────────────────────────────────────────
  COMPLIANCE: {
    AUDIT_LOG:        '/api/compliance/audit-log',
    RISK_ALERTS:      '/api/compliance/risk-alerts',
    GENERATE_DOC:     '/api/compliance/generate-doc',
    AI_GOVERNANCE:    '/api/compliance/ai-governance',
  },

  // ── Market Data ───────────────────────────────────────────────────────────
  MARKET: {
    NAV:              '/api/market/nav',
    NAV_SYMBOL:       (symbol) => `/api/market/nav/${symbol}`,
  },

  // ── System ────────────────────────────────────────────────────────────────
  SYSTEM: {
    HEALTH:           '/health',
  },
};
