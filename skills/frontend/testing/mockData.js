/**
 * mockData.js — Frontend mock data matching backend MOCK_CLIENTS.
 *
 * Used in:
 * - React Testing Library tests (render with known data)
 * - Storybook stories
 * - Development without backend
 *
 * Data mirrors backend mock_data.py — keep in sync.
 * Dependencies: constants.js (Tier 1)
 */

import { ROLES } from '../utils/constants.js';

// ─── Auth ─────────────────────────────────────────────────────────────────────

export const MOCK_TOKENS = {
  investor:   'mock-investor-jwt-token',
  rm:         'mock-rm-jwt-token',
  compliance: 'mock-compliance-jwt-token',
};

export const MOCK_USERS = {
  investor: {
    name: 'Priya Sharma',
    email: 'priya.sharma@demo.com',
    role: ROLES.INVESTOR,
    clientId: 'C001',
  },
  rm: {
    name: 'Rahul Mehta',
    email: 'rahul.mehta@wealthmanager.com',
    role: ROLES.RM,
    clientId: null,
  },
  compliance: {
    name: 'Anita Desai',
    email: 'anita.desai@wealthmanager.com',
    role: ROLES.COMPLIANCE,
    clientId: null,
  },
};

// ─── Portfolio ────────────────────────────────────────────────────────────────

export const MOCK_PORTFOLIO = {
  client_id: 'C001',
  total_invested: 2_400_000,
  current_value: 3_180_000,
  total_pnl: 780_000,
  xirr: 0.142,
  benchmark_xirr: 0.118,
  holdings: [
    {
      scheme_name: 'Mirae Asset Large Cap Fund',
      folio_number: 'F001',
      asset_class: 'equity',
      units: 1250.45,
      nav: 89.4,
      invested_amount: 800_000,
      current_value: 1_117_000,
      unrealized_pnl: 317_000,
      xirr: 0.158,
      purchase_date: '2021-04-01',
      is_ltcg_eligible: true,
      has_sip_active: true,
    },
    {
      scheme_name: 'HDFC Short Term Debt Fund',
      folio_number: 'F002',
      asset_class: 'debt',
      units: 5420.3,
      nav: 22.1,
      invested_amount: 900_000,
      current_value: 1_197_000,
      unrealized_pnl: 297_000,
      xirr: 0.072,
      purchase_date: '2020-10-15',
      is_ltcg_eligible: true,
      has_sip_active: false,
    },
    {
      scheme_name: 'SBI Gold ETF',
      folio_number: 'F003',
      asset_class: 'gold',
      units: 34.2,
      nav: 584.5,
      invested_amount: 700_000,
      current_value: 866_000,
      unrealized_pnl: 166_000,
      xirr: 0.092,
      purchase_date: '2022-01-10',
      is_ltcg_eligible: false,
      has_sip_active: false,
    },
  ],
  allocation_by_asset_class: {
    equity: 0.351,
    debt:   0.376,
    gold:   0.272,
  },
};

// ─── Goals ────────────────────────────────────────────────────────────────────

export const MOCK_GOALS = [
  {
    goal_id: 'G001',
    goal_name: 'Retirement Corpus',
    goal_type: 'retirement',
    target_amount: 30_000_000,
    current_corpus: 3_180_000,
    monthly_sip: 25_000,
    target_year: 2045,
    progress_pct: 10.6,
    status: 'on_track',
    feasibility_score: 88,
  },
  {
    goal_id: 'G002',
    goal_name: 'Children Education',
    goal_type: 'education',
    target_amount: 5_000_000,
    current_corpus: 1_200_000,
    monthly_sip: 12_000,
    target_year: 2032,
    progress_pct: 24.0,
    status: 'slightly_off',
    feasibility_score: 72,
  },
  {
    goal_id: 'G003',
    goal_name: 'Home Purchase',
    goal_type: 'home_purchase',
    target_amount: 8_000_000,
    current_corpus: 400_000,
    monthly_sip: 30_000,
    target_year: 2030,
    progress_pct: 5.0,
    status: 'needs_action',
    feasibility_score: 48,
  },
];

// ─── NAV History ─────────────────────────────────────────────────────────────

export const MOCK_NAV_HISTORY = Array.from({ length: 12 }, (_, i) => {
  const date = new Date(2025, i, 1);
  const base = 2_400_000;
  return {
    date: date.toISOString().split('T')[0],
    portfolio_value: Math.round(base * (1 + i * 0.065)),
    benchmark_value: Math.round(base * (1 + i * 0.052)),
  };
});

// ─── Chat History ─────────────────────────────────────────────────────────────

export const MOCK_CHAT_HISTORY = [
  {
    role: 'user',
    content: 'What is my current XIRR?',
    timestamp: '2025-10-01T10:00:00Z',
  },
  {
    role: 'assistant',
    content: 'Your portfolio XIRR is 14.20%, outperforming the Nifty 50 benchmark of 11.80%. *Disclaimer: Past performance is not indicative of future results.*',
    timestamp: '2025-10-01T10:00:05Z',
    confidence: 0.91,
  },
];

// ─── Clients (RM view) ───────────────────────────────────────────────────────

export const MOCK_CLIENTS = [
  {
    client_id: 'C001',
    name: 'Priya Sharma',
    email: 'priya.sharma@demo.com',
    segment: 'HNI',
    risk_profile: 'moderate',
    total_aum: 3_180_000,
    xirr: 0.142,
    days_since_review: 45,
    has_active_alerts: false,
  },
  {
    client_id: 'C002',
    name: 'Arjun Kapoor',
    email: 'arjun.kapoor@demo.com',
    segment: 'UHNI',
    risk_profile: 'aggressive',
    total_aum: 12_500_000,
    xirr: 0.187,
    days_since_review: 12,
    has_active_alerts: true,
  },
  {
    client_id: 'C003',
    name: 'Sunita Rao',
    email: 'sunita.rao@demo.com',
    segment: 'Mass_Affluent',
    risk_profile: 'conservative',
    total_aum: 850_000,
    xirr: 0.087,
    days_since_review: 120,
    has_active_alerts: true,
  },
];

// ─── Risk Alerts (Compliance) ────────────────────────────────────────────────

export const MOCK_RISK_ALERTS = [
  {
    alert_id: 'A001',
    client_id: 'C003',
    client_name: 'Sunita Rao',
    alert_type: 'no_review',
    priority: 'high',
    message: 'Client not reviewed in 120 days. SEBI IA requires annual review.',
    created_at: '2025-10-01T08:00:00Z',
  },
  {
    alert_id: 'A002',
    client_id: 'C002',
    client_name: 'Arjun Kapoor',
    alert_type: 'concentration_risk',
    priority: 'medium',
    message: 'Single stock concentration exceeds 20% threshold.',
    created_at: '2025-10-01T09:00:00Z',
  },
];
