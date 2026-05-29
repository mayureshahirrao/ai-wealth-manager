/**
 * PercentBadge.jsx — Positive/negative percentage display with color coding.
 *
 * Green for gains, red for losses. Includes +/- sign.
 * Used for XIRR, day change %, P&L %, goal progress.
 *
 * Dependencies: formatters.js (Tier 2)
 * Consumed by: Portfolio table, holdings view, performance summary
 *
 * @example
 * <PercentBadge value={0.134} />          // +13.40% in green
 * <PercentBadge value={-0.05} />          // -5.00% in red
 * <PercentBadge value={13.4} pill />      // pill variant
 */

import { formatPnLPercent } from '../utils/formatters.js';

/**
 * @param {{
 *   value: number,
 *   pill?: boolean,
 *   className?: string,
 * }} props
 */
export default function PercentBadge({ value, pill = false, className = '' }) {
  const { text, colorClass } = formatPnLPercent(value);

  const base = `font-medium tabular-nums ${colorClass} ${className}`;
  const pillClass = pill
    ? `inline-flex items-center rounded-full px-2 py-0.5 text-xs ${colorClass.replace('text-', 'bg-').replace('-600', '-50')} ${colorClass}`
    : `text-sm ${base}`;

  return <span className={pill ? pillClass : base}>{text}</span>;
}
