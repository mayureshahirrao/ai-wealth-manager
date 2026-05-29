/**
 * ErrorBoundary.jsx — React class-based error boundary.
 *
 * Catches render-time errors in the subtree and displays a fallback.
 * Does NOT catch async errors (use try/catch or React Query's error state).
 *
 * Dependencies: none (Tier 1)
 * Consumed by: App.jsx (root), individual dashboard sections
 *
 * @example
 * <ErrorBoundary fallback={<p>Chart failed to load.</p>}>
 *   <PortfolioChart data={data} />
 * </ErrorBoundary>
 */

import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    // In production, send to monitoring service
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center rounded-lg border border-red-200 bg-red-50 p-6 text-center">
          <div className="mb-2 text-2xl">⚠</div>
          <p className="text-sm font-medium text-red-800">Something went wrong</p>
          <p className="mt-1 text-xs text-red-600">
            {this.state.error?.message || 'An unexpected error occurred'}
          </p>
          <button
            onClick={this.handleReset}
            className="mt-4 rounded bg-red-600 px-4 py-1.5 text-xs font-medium text-white hover:bg-red-700"
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
