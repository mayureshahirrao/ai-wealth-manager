/**
 * chartHelpers.js — Transform API data into Recharts-compatible structures.
 *
 * All chart data transformation logic lives here. Components receive
 * ready-to-render data — no formatting or calculation in JSX.
 *
 * Dependencies: formatters.js, constants.js (Tier 2)
 * Consumed by: Portfolio chart, goal progress chart, NAV history chart
 */

import { ASSET_CLASS_COLORS, CHART_DEFAULTS } from './constants.js';
import { formatINRCompact, formatDate } from './formatters.js';

// ─── Portfolio Allocation Pie Chart ──────────────────────────────────────────

/**
 * Transform holdings data into Recharts PieChart format.
 *
 * @param {Array} holdings - Array of holding objects from API
 * @returns {Array} Recharts pie data
 *
 * @example
 * const pieData = holdingsToPieData(portfolio.holdings);
 * <PieChart><Pie data={pieData} .../></PieChart>
 */
export function holdingsToPieData(holdings = []) {
  // Group by asset class
  const grouped = holdings.reduce((acc, h) => {
    const cls = h.asset_class || 'equity';
    acc[cls] = (acc[cls] || 0) + (h.current_value || 0);
    return acc;
  }, {});

  const total = Object.values(grouped).reduce((s, v) => s + v, 0);

  return Object.entries(grouped).map(([assetClass, value]) => ({
    name: assetClass.charAt(0).toUpperCase() + assetClass.slice(1).replace('_', ' '),
    value: Math.round(value),
    pct: total > 0 ? ((value / total) * 100).toFixed(1) : '0.0',
    fill: ASSET_CLASS_COLORS[assetClass] || '#9CA3AF',
    assetClass,
  }));
}

// ─── NAV / Performance Line Chart ────────────────────────────────────────────

/**
 * Transform NAV history into Recharts LineChart format.
 *
 * @param {Array} navHistory - [{date, portfolio_value, benchmark_value}, ...]
 * @returns {Array} Recharts line data with formatted dates
 */
export function navHistoryToLineData(navHistory = []) {
  return navHistory.map((point) => ({
    date: formatDate(point.date),
    dateRaw: point.date,
    value: point.portfolio_value,
    valueFormatted: formatINRCompact(point.portfolio_value),
    benchmark: point.benchmark_value,
    benchmarkFormatted: formatINRCompact(point.benchmark_value),
  }));
}

// ─── Goal Progress Bar Chart ──────────────────────────────────────────────────

/**
 * Transform goals data into Recharts BarChart format.
 *
 * @param {Array} goals - Goal objects from API
 * @returns {Array} Recharts bar data
 */
export function goalsToBarData(goals = []) {
  return goals.map((goal) => ({
    name: goal.goal_name,
    current: Math.round(goal.current_corpus / 100_000),  // in Lakhs
    target: Math.round(goal.target_amount / 100_000),
    progress: goal.progress_pct || 0,
    status: goal.status,
    color: getGoalStatusColor(goal.status),
  }));
}

// ─── Retirement Projection Area Chart ────────────────────────────────────────

/**
 * Generate year-by-year projection data for retirement area chart.
 *
 * @param {number} currentCorpus - Current corpus in ₹
 * @param {number} monthlySIP - Monthly SIP in ₹
 * @param {number} yearsToRetirement - Years until retirement
 * @param {number} annualReturn - Expected return (e.g., 0.12)
 * @returns {Array} Recharts area data
 */
export function generateProjectionData(
  currentCorpus,
  monthlySIP,
  yearsToRetirement,
  annualReturn = 0.12,
) {
  const data = [];
  let corpus = currentCorpus;
  const monthlyRate = annualReturn / 12;
  const currentYear = new Date().getFullYear();

  for (let year = 0; year <= yearsToRetirement; year++) {
    data.push({
      year: currentYear + year,
      label: `${currentYear + year}`,
      corpus: Math.round(corpus),
      corpusLakhs: Math.round(corpus / 100_000 * 10) / 10,
    });

    // Grow existing corpus + add 12 months of SIP
    corpus = corpus * (1 + annualReturn);
    corpus += monthlySIP * 12 * (((1 + monthlyRate) ** 12 - 1) / monthlyRate);
  }

  return data;
}

// ─── SIP Step-Up Comparison Chart ────────────────────────────────────────────

/**
 * Generate data comparing flat SIP vs step-up SIP outcomes.
 */
export function generateStepUpComparison(
  monthlySIP,
  years,
  annualReturn = 0.12,
  stepUpRate = 0.10,
) {
  const data = [];
  const currentYear = new Date().getFullYear();

  let flatCorpus = 0;
  let stepUpCorpus = 0;
  let currentSIP = monthlySIP;
  const monthlyRate = annualReturn / 12;

  for (let year = 1; year <= years; year++) {
    const monthsRemaining = (years - year) * 12;
    const flatFV = monthlySIP * (((1 + monthlyRate) ** (year * 12) - 1) / monthlyRate) * (1 + monthlyRate);
    flatCorpus = flatFV;

    // Step-up compound
    stepUpCorpus += currentSIP * 12 * (((1 + monthlyRate) ** (years - year + 1) * 12 - 1) / monthlyRate);
    currentSIP *= (1 + stepUpRate);

    data.push({
      year: currentYear + year,
      flatSIP: Math.round(flatCorpus / 100_000),
      stepUpSIP: Math.round(stepUpCorpus / 100_000),
    });
  }

  return data;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function getGoalStatusColor(status) {
  const colors = {
    on_track:      CHART_DEFAULTS.POSITIVE_COLOR,
    slightly_off:  '#F59E0B',
    needs_action:  '#F97316',
    at_risk:       CHART_DEFAULTS.NEGATIVE_COLOR,
  };
  return colors[status] || '#6B7280';
}

/**
 * Custom tooltip formatter for INR values in Recharts.
 * Pass to <Tooltip formatter={inrTooltipFormatter} />
 */
export function inrTooltipFormatter(value, name) {
  return [`₹${value} L`, name];
}
