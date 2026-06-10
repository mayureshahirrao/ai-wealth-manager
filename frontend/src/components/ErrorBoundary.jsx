/**
 * ErrorBoundary.jsx — React class-based error boundary.
 *
 * Catches render-time errors in the subtree and displays a fallback.
 * Does NOT catch async errors (use try/catch or React Query's error state).
 *
 * Props:
 *   fallback  — custom fallback element (optional)
 *   fullPage  — if true, centers the error UI to fill the viewport (default false)
 *
 * Dependencies: none (Tier 1)
 * Consumed by: App.jsx (root), individual dashboard layouts
 *
 * @example
 * // Root-level (catch any crash)
 * <ErrorBoundary fullPage>
 *   <App />
 * </ErrorBoundary>
 *
 * // Component-level (graceful chart failure)
 * <ErrorBoundary fallback={<p>Chart failed to load.</p>}>
 *   <PortfolioChart data={data} />
 * </ErrorBoundary>
 */

import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    this.setState({ errorInfo: info });
    // In production, send to Sentry/LogRocket/Datadog here
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    // Custom fallback provided by parent
    if (this.props.fallback) {
      return this.props.fallback;
    }

    const { error, errorInfo } = this.state;
    const isDev = typeof import.meta !== 'undefined' && import.meta.env?.DEV;

    // Full-page layout (for root-level boundary)
    if (this.props.fullPage) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-8">
          <div className="max-w-lg w-full bg-white rounded-xl shadow-sm border border-red-200 p-8 text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">Something went wrong</h2>
            <p className="text-gray-500 text-sm mb-6">
              An unexpected error occurred. Your data is safe — please try refreshing.
            </p>
            {isDev && error && (
              <details className="text-left mb-6 bg-red-50 rounded-lg p-4">
                <summary className="text-xs font-mono text-red-700 cursor-pointer select-none">
                  Error details (dev only)
                </summary>
                <pre className="mt-2 text-xs text-red-600 overflow-auto whitespace-pre-wrap break-words max-h-48">
                  {error.toString()}
                  {errorInfo?.componentStack}
                </pre>
              </details>
            )}
            <div className="flex gap-3 justify-center">
              <button
                onClick={this.handleReset}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Reload Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    // Inline / section-level fallback
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-red-200 bg-red-50 p-6 text-center">
        <div className="mb-2 text-2xl">⚠</div>
        <p className="text-sm font-medium text-red-800">Something went wrong</p>
        <p className="mt-1 text-xs text-red-600">
          {error?.message || 'An unexpected error occurred'}
        </p>
        {isDev && errorInfo && (
          <details className="mt-2 text-left w-full">
            <summary className="text-xs font-mono text-red-500 cursor-pointer">Stack trace</summary>
            <pre className="mt-1 text-xs text-red-400 overflow-auto whitespace-pre-wrap max-h-32">
              {errorInfo.componentStack}
            </pre>
          </details>
        )}
        <button
          onClick={this.handleReset}
          className="mt-4 rounded bg-red-600 px-4 py-1.5 text-xs font-medium text-white hover:bg-red-700"
        >
          Try again
        </button>
      </div>
    );
  }
}
