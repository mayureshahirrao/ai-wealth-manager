/**
 * formatters.js — Display formatters for Indian financial data.
 *
 * All formatting of ₹ amounts, percentages, dates, and XIRR must
 * go through these functions. Never format inline in components.
 *
 * Dependencies: constants.js (Tier 1)
 * Consumed by: All components displaying financial data, chartHelpers.js
 */

// ─── INR Formatters ───────────────────────────────────────────────────────────

/**
 * Format INR amount using Indian convention (Lakh/Crore).
 *
 * @param {number} amount - Amount in rupees
 * @param {number} [decimals=2] - Decimal places
 * @returns {string} Formatted string like "₹42.50 L" or "₹2.30 Cr"
 *
 * @example
 * formatINR(4200000)   // "₹42.00 L"
 * formatINR(23000000)  // "₹2.30 Cr"
 * formatINR(95000)     // "₹95,000"
 * formatINR(-500000)   // "-₹5.00 L"
 */
export function formatINR(amount, decimals = 2) {
  if (amount === null || amount === undefined || isNaN(amount)) return '₹—';
  const sign = amount < 0 ? '-' : '';
  const abs = Math.abs(amount);

  if (abs >= 10_000_000) return `${sign}₹${(abs / 10_000_000).toFixed(decimals)} Cr`;
  if (abs >= 100_000)    return `${sign}₹${(abs / 100_000).toFixed(decimals)} L`;
  return `${sign}₹${abs.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
}

/**
 * Format amount in Indian numbering (2-2-3 grouping).
 * @example formatINRFull(1000000) → "₹10,00,000"
 */
export function formatINRFull(amount) {
  if (amount === null || amount === undefined) return '₹—';
  return `₹${Math.round(amount).toLocaleString('en-IN')}`;
}

/**
 * Format short INR for compact displays (charts, badges).
 * @example formatINRCompact(4200000) → "₹42L"
 */
export function formatINRCompact(amount) {
  if (amount === null || amount === undefined) return '₹—';
  const abs = Math.abs(amount);
  const sign = amount < 0 ? '-' : '';
  if (abs >= 10_000_000) return `${sign}₹${(abs / 10_000_000).toFixed(1)}Cr`;
  if (abs >= 100_000)    return `${sign}₹${(abs / 100_000).toFixed(1)}L`;
  return `${sign}₹${(abs / 1000).toFixed(0)}K`;
}

// ─── Percentage Formatters ────────────────────────────────────────────────────

/**
 * Format XIRR/return percentage.
 * @example formatPercent(0.134) → "13.40%"
 */
export function formatPercent(value, decimals = 2) {
  if (value === null || value === undefined || isNaN(value)) return '—%';
  // Handle both decimal (0.13) and already-percent (13.4) inputs
  const pct = Math.abs(value) > 1 ? value : value * 100;
  return `${pct.toFixed(decimals)}%`;
}

/**
 * Format P&L percentage with sign and color class.
 * @returns {{ text: string, colorClass: string }}
 */
export function formatPnLPercent(value) {
  if (value === null || value === undefined) return { text: '—', colorClass: 'text-gray-500' };
  const pct = Math.abs(value) > 1 ? value : value * 100;
  const sign = pct >= 0 ? '+' : '';
  return {
    text: `${sign}${pct.toFixed(2)}%`,
    colorClass: pct >= 0 ? 'text-green-600' : 'text-red-600',
  };
}

// ─── Date Formatters ──────────────────────────────────────────────────────────

/**
 * Format date in Indian DD MMM YYYY format.
 * @example formatDate("2024-03-15") → "15 Mar 2024"
 */
export function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

/**
 * Format relative time for "last reviewed" displays.
 * @example formatDaysAgo(45) → "45 days ago"
 */
export function formatDaysAgo(days) {
  if (days === null || days === undefined) return 'Never';
  if (days === 0) return 'Today';
  if (days === 1) return 'Yesterday';
  if (days < 30)  return `${days} days ago`;
  if (days < 365) return `${Math.floor(days / 30)} months ago`;
  return `${Math.floor(days / 365)} years ago`;
}

// ─── Financial Metric Formatters ──────────────────────────────────────────────

/**
 * Format XIRR for display (accepts decimal or percent).
 * @example formatXIRR(0.134) → "13.40%"
 */
export function formatXIRR(xirr) {
  return formatPercent(xirr);
}

/**
 * Format confidence score as percentage badge data.
 */
export function formatConfidence(score) {
  if (score === null || score === undefined) return { text: '—', level: 'unknown' };
  const pct = score <= 1 ? score * 100 : score;
  const level = pct >= 85 ? 'high' : pct >= 65 ? 'medium' : 'low';
  return { text: `${pct.toFixed(0)}%`, level };
}

/**
 * Format goal feasibility score.
 */
export function formatFeasibilityScore(score) {
  if (score >= 90) return { label: 'On Track',     color: 'text-green-600',  bg: 'bg-green-50' };
  if (score >= 70) return { label: 'Slightly Off', color: 'text-amber-600',  bg: 'bg-amber-50' };
  if (score >= 40) return { label: 'Needs Action', color: 'text-orange-600', bg: 'bg-orange-50' };
  return            { label: 'At Risk',          color: 'text-red-600',    bg: 'bg-red-50' };
}
