/**
 * testUtils.jsx — React Testing Library render wrappers.
 *
 * Provides:
 * - renderWithProviders(): wraps component in QueryClient + AuthProvider + Router
 * - createMockAuthContext(): returns mock auth values for any role
 * - mockApiResponse(): MSW-style fetch mock helper
 *
 * Dependencies: mockData.js, useAuth.js (Tier 5 — test only)
 * Import in tests: import { renderWithProviders } from '../testing/testUtils.jsx';
 */

import React from 'react';
import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { AuthContext } from '../hooks/useAuth.js';
import { MOCK_USERS, MOCK_TOKENS } from './mockData.js';
import { ROLES } from '../utils/constants.js';

// ─── Query Client (no retries in tests) ──────────────────────────────────────

function buildTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: Infinity,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

// ─── Auth Context Mock ────────────────────────────────────────────────────────

/**
 * Create a mock auth context value for any role.
 *
 * @param {'investor'|'rm'|'compliance'} role
 * @param {Object} overrides - Merge into context
 * @returns {Object} AuthContext value
 */
export function createMockAuthContext(role = 'investor', overrides = {}) {
  const user = MOCK_USERS[role];
  return {
    user,
    role: user.role,
    isLoading: false,
    error: null,
    isAuthenticated: true,
    isInvestor:  user.role === ROLES.INVESTOR,
    isRM:        user.role === ROLES.RM,
    isCompliance: user.role === ROLES.COMPLIANCE,
    clientId: user.clientId,
    login:  jest.fn().mockResolvedValue({ success: true, role: user.role }),
    logout: jest.fn(),
    ...overrides,
  };
}

// ─── Render Wrapper ───────────────────────────────────────────────────────────

/**
 * renderWithProviders — wraps UI in all required providers.
 *
 * @param {React.ReactElement} ui
 * @param {{
 *   role?: 'investor'|'rm'|'compliance',
 *   authOverrides?: Object,
 *   initialEntries?: string[],
 *   queryClient?: QueryClient,
 * }} options
 */
export function renderWithProviders(
  ui,
  {
    role = 'investor',
    authOverrides = {},
    initialEntries = ['/'],
    queryClient,
  } = {},
) {
  const client = queryClient || buildTestQueryClient();
  const authValue = createMockAuthContext(role, authOverrides);

  function Wrapper({ children }) {
    return (
      <QueryClientProvider client={client}>
        <AuthContext.Provider value={authValue}>
          <MemoryRouter initialEntries={initialEntries}>
            {children}
          </MemoryRouter>
        </AuthContext.Provider>
      </QueryClientProvider>
    );
  }

  return {
    ...render(ui, { wrapper: Wrapper }),
    queryClient: client,
    authValue,
  };
}

// ─── Fetch Mock Helpers ───────────────────────────────────────────────────────

/**
 * Mock a single fetch call to return data.
 * Restores global.fetch after the test automatically when used with afterEach.
 *
 * @param {Object} data - Response body (will be JSON-stringified)
 * @param {number} status
 */
export function mockFetchResponse(data, status = 200) {
  global.fetch = jest.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
    body: {
      getReader: () => ({
        read: jest.fn()
          .mockResolvedValueOnce({
            done: false,
            value: new TextEncoder().encode(`data: ${JSON.stringify({ type: 'done', confidence: 0.9 })}\n\n`),
          })
          .mockResolvedValueOnce({ done: true }),
      }),
    },
  });
}

/**
 * Mock a streaming SSE fetch response.
 *
 * @param {string[]} deltaTokens - Text tokens to stream as delta events
 */
export function mockSSEStream(deltaTokens = []) {
  const chunks = [
    ...deltaTokens.map((text) =>
      `data: ${JSON.stringify({ type: 'delta', text })}\n\n`
    ),
    `data: ${JSON.stringify({ type: 'done', confidence: 0.85 })}\n\n`,
  ];

  let callCount = 0;
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    status: 200,
    body: {
      getReader: () => ({
        read: jest.fn().mockImplementation(() => {
          if (callCount < chunks.length) {
            return Promise.resolve({
              done: false,
              value: new TextEncoder().encode(chunks[callCount++]),
            });
          }
          return Promise.resolve({ done: true });
        }),
      }),
    },
  });
}
