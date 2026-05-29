/**
 * INRAmount.jsx — Consistent INR display component.
 *
 * Always renders currency through formatters.js — never format inline.
 * Supports compact (₹42L), full (₹42.00 L), and Indian numbering (₹42,00,000) variants.
 *
 * Dependencies: formatters.js (Tier 2)
 * Consumed by: All components showing ₹ amounts
 *
 * @example
 * <INRAmount value={4200000} />               // ₹42.00 L
 * <INRAmount value={4200000} variant="compact" /> // ₹42L
 * <INRAmount value={-500000} className="text-red-600" />
 */

import { formatINR, formatINRCompact, formatINRFull } from '../utils/formatters.js';

const VARIANTS = {
  default: formatINR,
  compact: formatINRCompact,
  full:    formatINRFull,
};

/**
 * @param {{
 *   value: number,
 *   variant?: 'default'|'compact'|'full',
 *   decimals?: number,
 *   className?: string,
 *   as?: keyof JSX.IntrinsicElements
 * }} props
 */
export default function INRAmount({
  value,
  variant = 'default',
  decimals = 2,
  className = '',
  as: Tag = 'span',
}) {
  const formatter = VARIANTS[variant] || formatINR;
  const formatted = variant === 'default'
    ? formatter(value, decimals)
    : formatter(value);

  return <Tag className={className}>{formatted}</Tag>;
}
