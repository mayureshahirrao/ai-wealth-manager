/**
 * LoadingSpinner.jsx — Reusable loading indicator.
 *
 * Variants: 'sm' | 'md' | 'lg' | 'page'
 * 'page' centers in the full viewport (for route-level loading).
 *
 * Dependencies: none (Tier 1)
 * Consumed by: All async data views
 */

const SIZE_CLASSES = {
  sm:   'h-4 w-4 border-2',
  md:   'h-8 w-8 border-2',
  lg:   'h-12 w-12 border-4',
  page: 'h-16 w-16 border-4',
};

/**
 * @param {{ size?: 'sm'|'md'|'lg'|'page', label?: string, className?: string }} props
 */
export default function LoadingSpinner({ size = 'md', label = 'Loading...', className = '' }) {
  const spinner = (
    <div
      role="status"
      aria-label={label}
      className={`${className} inline-flex flex-col items-center gap-2`}
    >
      <div
        className={`
          ${SIZE_CLASSES[size] || SIZE_CLASSES.md}
          animate-spin rounded-full
          border-blue-200 border-t-blue-600
        `}
      />
      {label && size === 'page' && (
        <span className="text-sm text-gray-500">{label}</span>
      )}
    </div>
  );

  if (size === 'page') {
    return (
      <div className="flex h-full min-h-[60vh] w-full items-center justify-center">
        {spinner}
      </div>
    );
  }

  return spinner;
}
