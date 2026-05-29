/**
 * useApi.js — React Query wrappers for all API calls.
 *
 * Provides:
 * - useQuery wrappers with standard stale/cache times
 * - useMutation wrappers with optimistic updates
 * - Role-aware data fetching (clientId from useAuth)
 *
 * Dependencies: apiClient.js, endpoints.js, useAuth.js (Tier 3)
 * Consumed by: All dashboard components, portfolio views, goal views
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/apiClient.js';
import { ENDPOINTS } from '../api/endpoints.js';
import { POLLING } from '../utils/constants.js';
import { useAuth } from './useAuth.js';

// ─── Query Key Factory ─────────────────────────────────────────────────────────

export const queryKeys = {
  portfolio:     (clientId) => ['portfolio', clientId],
  goals:         (clientId) => ['goals', clientId],
  taxSummary:    (clientId) => ['taxSummary', clientId],
  navHistory:    (clientId) => ['navHistory', clientId],
  performance:   (clientId) => ['performance', clientId],
  chatHistory:   (clientId) => ['chatHistory', clientId],
  clients:       () => ['clients'],
  clientDetail:  (clientId) => ['client', clientId],
  nextActions:   () => ['nextActions'],
  meetingPrep:   (clientId) => ['meetingPrep', clientId],
  clientAlerts:  (clientId) => ['clientAlerts', clientId],
  auditLog:      () => ['auditLog'],
  riskAlerts:    () => ['riskAlerts'],
  financialPlan: (clientId) => ['financialPlan', clientId],
  marketNav:     () => ['marketNav'],
};

// ─── Standard Query Config ────────────────────────────────────────────────────

const PORTFOLIO_QUERY_CONFIG = {
  staleTime: POLLING.PORTFOLIO_MS,
  refetchInterval: POLLING.PORTFOLIO_MS,
};

const MARKET_QUERY_CONFIG = {
  staleTime: POLLING.MARKET_DATA_MS,
  refetchInterval: POLLING.MARKET_DATA_MS,
};

const ALERTS_QUERY_CONFIG = {
  staleTime: POLLING.ALERTS_MS,
  refetchInterval: POLLING.ALERTS_MS,
};

const STATIC_QUERY_CONFIG = {
  staleTime: Infinity,
  refetchInterval: false,
};

// ─── Portfolio Hooks ──────────────────────────────────────────────────────────

export function usePortfolio(clientId) {
  return useQuery({
    queryKey: queryKeys.portfolio(clientId),
    queryFn: () => apiClient.get(ENDPOINTS.CLIENTS.PORTFOLIO(clientId)),
    enabled: !!clientId,
    ...PORTFOLIO_QUERY_CONFIG,
  });
}

export function useGoals(clientId) {
  return useQuery({
    queryKey: queryKeys.goals(clientId),
    queryFn: () => apiClient.get(ENDPOINTS.CLIENTS.GOALS(clientId)),
    enabled: !!clientId,
    ...PORTFOLIO_QUERY_CONFIG,
  });
}

export function useTaxSummary(clientId) {
  return useQuery({
    queryKey: queryKeys.taxSummary(clientId),
    queryFn: () => apiClient.get(ENDPOINTS.CLIENTS.TAX_SUMMARY(clientId)),
    enabled: !!clientId,
    ...STATIC_QUERY_CONFIG,
  });
}

export function useNAVHistory(clientId) {
  return useQuery({
    queryKey: queryKeys.navHistory(clientId),
    queryFn: () => apiClient.get(ENDPOINTS.CLIENTS.NAV_HISTORY(clientId)),
    enabled: !!clientId,
    ...PORTFOLIO_QUERY_CONFIG,
  });
}

export function usePerformance(clientId) {
  return useQuery({
    queryKey: queryKeys.performance(clientId),
    queryFn: () => apiClient.get(ENDPOINTS.CLIENTS.PERFORMANCE(clientId)),
    enabled: !!clientId,
    ...PORTFOLIO_QUERY_CONFIG,
  });
}

// ─── Investor Self-Service Hooks (clientId from auth) ─────────────────────────

export function useMyPortfolio() {
  const { clientId } = useAuth();
  return usePortfolio(clientId);
}

export function useMyGoals() {
  const { clientId } = useAuth();
  return useGoals(clientId);
}

export function useMyTaxSummary() {
  const { clientId } = useAuth();
  return useTaxSummary(clientId);
}

// ─── Chat History Hook ────────────────────────────────────────────────────────

export function useChatHistory(clientId) {
  return useQuery({
    queryKey: queryKeys.chatHistory(clientId),
    queryFn: () => apiClient.get(ENDPOINTS.CHAT.HISTORY(clientId)),
    enabled: !!clientId,
    staleTime: 60_000,
  });
}

// ─── RM Hooks ─────────────────────────────────────────────────────────────────

export function useClients() {
  return useQuery({
    queryKey: queryKeys.clients(),
    queryFn: () => apiClient.get(ENDPOINTS.CLIENTS.LIST),
    staleTime: 120_000,
  });
}

export function useClientDetail(clientId) {
  return useQuery({
    queryKey: queryKeys.clientDetail(clientId),
    queryFn: () => apiClient.get(ENDPOINTS.CLIENTS.DETAIL(clientId)),
    enabled: !!clientId,
    staleTime: 120_000,
  });
}

export function useNextActions() {
  return useQuery({
    queryKey: queryKeys.nextActions(),
    queryFn: () => apiClient.get(ENDPOINTS.RM.NEXT_ACTIONS),
    ...ALERTS_QUERY_CONFIG,
  });
}

export function useMeetingPrep(clientId) {
  return useQuery({
    queryKey: queryKeys.meetingPrep(clientId),
    queryFn: () => apiClient.get(ENDPOINTS.RM.MEETING_PREP(clientId)),
    enabled: !!clientId,
    ...STATIC_QUERY_CONFIG,
  });
}

export function useClientAlerts(clientId) {
  return useQuery({
    queryKey: queryKeys.clientAlerts(clientId),
    queryFn: () => apiClient.get(ENDPOINTS.RM.CLIENT_ALERTS(clientId)),
    enabled: !!clientId,
    ...ALERTS_QUERY_CONFIG,
  });
}

// ─── Financial Plan Hooks ─────────────────────────────────────────────────────

export function useFinancialPlan(clientId) {
  return useQuery({
    queryKey: queryKeys.financialPlan(clientId),
    queryFn: () => apiClient.get(ENDPOINTS.FINANCIAL_PLAN.GET(clientId)),
    enabled: !!clientId,
    ...STATIC_QUERY_CONFIG,
  });
}

export function useGenerateFinancialPlan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload) => apiClient.post(ENDPOINTS.FINANCIAL_PLAN.GENERATE, payload),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.financialPlan(variables.client_id) });
    },
  });
}

// ─── Compliance Hooks ─────────────────────────────────────────────────────────

export function useAuditLog(params = {}) {
  return useQuery({
    queryKey: [...queryKeys.auditLog(), params],
    queryFn: () => apiClient.get(ENDPOINTS.COMPLIANCE.AUDIT_LOG, { params }),
    staleTime: 30_000,
  });
}

export function useRiskAlerts() {
  return useQuery({
    queryKey: queryKeys.riskAlerts(),
    queryFn: () => apiClient.get(ENDPOINTS.COMPLIANCE.RISK_ALERTS),
    ...ALERTS_QUERY_CONFIG,
  });
}

export function useGenerateComplianceDoc() {
  return useMutation({
    mutationFn: (payload) => apiClient.post(ENDPOINTS.COMPLIANCE.GENERATE_DOC, payload),
  });
}

// ─── Market Data Hooks ────────────────────────────────────────────────────────

export function useMarketNAV() {
  return useQuery({
    queryKey: queryKeys.marketNav(),
    queryFn: () => apiClient.get(ENDPOINTS.MARKET.NAV),
    ...MARKET_QUERY_CONFIG,
  });
}
