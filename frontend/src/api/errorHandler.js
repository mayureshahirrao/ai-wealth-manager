/**
 * errorHandler.js — Global API error handling utilities for the frontend.
 *
 * Provides:
 * - Human-readable error messages from API error codes
 * - Toast notification helpers (returns message strings, UI-lib agnostic)
 * - React Query global error handler config
 *
 * Dependencies: apiClient.js (Tier 3)
 * Consumed by: QueryClient config in main.jsx, components needing error display
 */

// ─── Error Code → User Message Map ───────────────────────────────────────────

const ERROR_MESSAGES = {
  // Auth
  INVALID_CREDENTIALS:    'Incorrect email or password. Please try again.',
  TOKEN_EXPIRED:          'Your session has expired. Please log in again.',
  UNAUTHORIZED:           'You are not authorized to perform this action.',
  FORBIDDEN:              'Access denied. Insufficient permissions.',

  // Client / Data
  CLIENT_NOT_FOUND:       'Client record not found.',
  NOT_FOUND:              'The requested resource was not found.',
  VALIDATION_ERROR:       'Please check your inputs and try again.',
  INVALID_PAN:            'PAN format is invalid. Expected: ABCDE1234F.',

  // AI / Agent
  AI_TOOL_EXECUTION_ERROR: 'The AI tool encountered an error. Please retry.',
  AGENT_EXECUTION_ERROR:   'The AI agent failed to complete. Please retry.',
  RAG_RETRIEVAL_ERROR:     'Knowledge base search failed.',
  LOW_CONFIDENCE:          'AI confidence is low — please consult your advisor.',

  // Financial
  PORTFOLIO_CALCULATION_ERROR: 'Portfolio calculation error. Data may be incomplete.',
  INSUFFICIENT_DATA:           'Not enough data to perform this calculation.',

  // Compliance
  SEBI_VALIDATION_ERROR:  'Response blocked: SEBI compliance check failed.',
  COMPLIANCE_VIOLATION:   'This action would violate compliance rules.',

  // System
  DATABASE_ERROR:         'Database error. Please try again shortly.',
  UNKNOWN_ERROR:          'An unexpected error occurred. Please try again.',
};

// ─── Public Helpers ───────────────────────────────────────────────────────────

/**
 * Resolve a user-friendly message from an enriched API error.
 * Falls back gracefully for unknown codes.
 *
 * @param {Error} error - Error from apiClient interceptor
 * @returns {string}
 */
export function getErrorMessage(error) {
  if (!error) return ERROR_MESSAGES.UNKNOWN_ERROR;

  // Check specific error code first
  if (error.errorCode && ERROR_MESSAGES[error.errorCode]) {
    return ERROR_MESSAGES[error.errorCode];
  }

  // Network-level failures
  if (error.message === 'Network Error') {
    return 'Cannot reach the server. Check your internet connection.';
  }

  if (error.status === 503 || error.status === 502) {
    return 'Server is temporarily unavailable. Please try again in a moment.';
  }

  // Fall back to raw message
  return error.message || ERROR_MESSAGES.UNKNOWN_ERROR;
}

/**
 * Determine if an error should trigger a logout redirect.
 * Only for genuine auth failures, not 403 permission errors.
 *
 * @param {Error} error
 * @returns {boolean}
 */
export function isAuthError(error) {
  return (
    error?.status === 401 ||
    error?.errorCode === 'TOKEN_EXPIRED' ||
    error?.errorCode === 'INVALID_TOKEN'
  );
}

/**
 * Build a React Query global error handler.
 * Pass to QueryClient's defaultOptions.queries.onError and mutations.onError.
 *
 * @param {Function} onAuthFailure - Called when session expires
 * @param {Function} onError       - Generic error callback (e.g., show toast)
 * @returns {{ onError: Function }}
 */
export function buildQueryErrorHandlers(onAuthFailure, onError) {
  const handler = (error) => {
    if (isAuthError(error)) {
      onAuthFailure?.();
    } else {
      onError?.(getErrorMessage(error));
    }
  };

  return {
    queries:   { onError: handler },
    mutations: { onError: handler },
  };
}
