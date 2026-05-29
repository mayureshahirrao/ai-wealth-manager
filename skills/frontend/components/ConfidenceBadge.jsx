/**
 * ConfidenceBadge.jsx — AI response confidence indicator.
 *
 * Shows HIGH / MEDIUM / LOW confidence from the AI agent.
 * High (≥85%): green. Medium (≥65%): amber. Low (<65%): red.
 * Optionally shows a tooltip explaining what confidence means.
 *
 * Dependencies: formatters.js, constants.js (Tier 2)
 * Consumed by: ChatInterface, AI-generated report sections
 *
 * @example
 * <ConfidenceBadge score={0.87} />   // HIGH 87%
 * <ConfidenceBadge score={0.6} />    // MEDIUM 60%
 */

import { formatConfidence } from '../utils/formatters.js';

const LEVEL_STYLES = {
  high:    'bg-green-50 text-green-700 ring-green-600/20',
  medium:  'bg-amber-50 text-amber-700 ring-amber-600/20',
  low:     'bg-red-50 text-red-700 ring-red-600/20',
  unknown: 'bg-gray-50 text-gray-600 ring-gray-500/20',
};

const LEVEL_LABELS = {
  high:    'HIGH',
  medium:  'MEDIUM',
  low:     'LOW',
  unknown: '—',
};

/**
 * @param {{
 *   score: number,
 *   showLabel?: boolean,
 *   className?: string,
 * }} props
 */
export default function ConfidenceBadge({ score, showLabel = true, className = '' }) {
  const { text, level } = formatConfidence(score);
  const styles = LEVEL_STYLES[level] || LEVEL_STYLES.unknown;

  return (
    <span
      className={`
        inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium
        ring-1 ring-inset ${styles} ${className}
      `}
      title="AI confidence score — reflects data completeness and response quality"
    >
      {showLabel && <span className="opacity-60">{LEVEL_LABELS[level]}</span>}
      <span>{text}</span>
    </span>
  );
}
