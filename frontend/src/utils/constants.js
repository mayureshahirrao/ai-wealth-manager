/**
 * constants.js — All frontend constants.
 *
 * Never use raw strings for roles, asset classes, or URLs in components.
 * Import from here to ensure consistency and catch typos at development time.
 *
 * Dependencies: None (Tier 0)
 * Consumed by: All components, hooks, formatters
 */

// ─── User Roles ───────────────────────────────────────────────────────────────
export const ROLES = {
  INVESTOR: 'investor',
  RM: 'rm',
  COMPLIANCE: 'compliance',
};

// ─── Asset Classes ────────────────────────────────────────────────────────────
export const ASSET_CLASSES = {
  EQUITY: 'equity',
  DEBT: 'debt',
  GOLD: 'gold',
  INTERNATIONAL: 'international',
  CASH: 'cash',
  CRYPTO: 'crypto',
  REAL_ESTATE: 'real_estate',
};

// Chart colors for each asset class (Tailwind-inspired palette)
export const ASSET_CLASS_COLORS = {
  equity:        '#3B82F6',   // blue-500
  debt:          '#8B5CF6',   // violet-500
  gold:          '#F59E0B',   // amber-500
  international: '#10B981',   // emerald-500
  cash:          '#6B7280',   // gray-500
  crypto:        '#EF4444',   // red-500
  real_estate:   '#F97316',   // orange-500
};

// ─── Goal Types ───────────────────────────────────────────────────────────────
export const GOAL_TYPES = {
  RETIREMENT:      'retirement',
  HOME_PURCHASE:   'home_purchase',
  CHILD_EDUCATION: 'child_education',
  EMERGENCY_FUND:  'emergency_fund',
  VACATION:        'vacation',
  WEALTH_CREATION: 'wealth_creation',
};

export const GOAL_ICONS = {
  retirement:      '🏖️',
  home_purchase:   '🏠',
  child_education: '🎓',
  emergency_fund:  '🛡️',
  vacation:        '✈️',
  wealth_creation: '📈',
};

// ─── Risk Profiles ────────────────────────────────────────────────────────────
export const RISK_PROFILES = {
  CONSERVATIVE:           'conservative',
  MODERATE:               'moderate',
  MODERATELY_AGGRESSIVE:  'moderately_aggressive',
  AGGRESSIVE:             'aggressive',
};

export const RISK_PROFILE_COLORS = {
  conservative:          '#10B981',   // green
  moderate:              '#3B82F6',   // blue
  moderately_aggressive: '#F59E0B',   // amber
  aggressive:            '#EF4444',   // red
};

// ─── Alert Priority Colors ────────────────────────────────────────────────────
export const ALERT_PRIORITY_COLORS = {
  critical: '#EF4444',   // red-500
  high:     '#F97316',   // orange-500
  medium:   '#F59E0B',   // amber-500
  low:      '#6B7280',   // gray-500
};

// ─── Wealth Segments ──────────────────────────────────────────────────────────
export const SEGMENTS = {
  RETAIL:         'Retail',
  MASS_AFFLUENT:  'Mass Affluent',
  HNW:            'HNW',
  UHNW:           'UHNW',
};

export const SEGMENT_COLORS = {
  'Retail':        '#6B7280',
  'Mass Affluent': '#3B82F6',
  'HNW':           '#8B5CF6',
  'UHNW':          '#F59E0B',
};

// ─── AI Confidence Thresholds ──────────────────────────────────────────────────
export const CONFIDENCE = {
  HIGH:    0.85,   // Green badge
  MEDIUM:  0.65,   // Amber badge
  LOW:     0.0,    // Red badge — escalate to human
};

// ─── Chart Defaults ───────────────────────────────────────────────────────────
export const CHART_DEFAULTS = {
  LINE_COLOR:         '#3B82F6',
  BENCHMARK_COLOR:    '#9CA3AF',
  POSITIVE_COLOR:     '#10B981',
  NEGATIVE_COLOR:     '#EF4444',
  ANIMATION_DURATION: 500,
};

// ─── Demo Client Personas ─────────────────────────────────────────────────────
export const DEMO_INVESTORS = [
  { email: 'priya.sharma@demo.com',  name: 'Priya Sharma',  segment: 'Mass Affluent' },
  { email: 'rajesh.gupta@demo.com',  name: 'Rajesh Gupta',  segment: 'Mass Affluent' },
  { email: 'neha.khanna@demo.com',   name: 'Neha Khanna',   segment: 'HNW' },
  { email: 'aarav.singh@demo.com',   name: 'Aarav Singh',   segment: 'Retail' },
  { email: 'sushma.reddy@demo.com',  name: 'Sushma Reddy',  segment: 'HNW' },
];

export const DEMO_PASSWORD = 'demo1234';

// ─── Polling Intervals ────────────────────────────────────────────────────────
export const POLLING = {
  MARKET_DATA_MS:   30_000,    // 30s for NAV refresh
  ALERTS_MS:        60_000,    // 60s for compliance alerts
  PORTFOLIO_MS:     300_000,   // 5min for portfolio refresh
};
