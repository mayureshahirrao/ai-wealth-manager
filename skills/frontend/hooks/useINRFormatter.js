/**
 * useINRFormatter.js — Convenience hook wrapping all INR formatters.
 *
 * Avoids importing multiple formatter functions in every component.
 * Returns a stable object of formatting functions (no re-renders).
 *
 * Dependencies: formatters.js (Tier 2)
 * Consumed by: Any component displaying financial figures
 *
 * @example
 * const { formatINR, formatPercent, formatDate } = useINRFormatter();
 * <span>{formatINR(portfolio.total_value)}</span>
 */

import { useMemo } from 'react';
import {
  formatINR,
  formatINRFull,
  formatINRCompact,
  formatPercent,
  formatPnLPercent,
  formatDate,
  formatDaysAgo,
  formatXIRR,
  formatConfidence,
  formatFeasibilityScore,
} from '../utils/formatters.js';

export function useINRFormatter() {
  // useMemo so the returned object reference is stable across renders
  return useMemo(() => ({
    formatINR,
    formatINRFull,
    formatINRCompact,
    formatPercent,
    formatPnLPercent,
    formatDate,
    formatDaysAgo,
    formatXIRR,
    formatConfidence,
    formatFeasibilityScore,
  }), []);
}
