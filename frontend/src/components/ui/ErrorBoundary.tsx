'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * ErrorBoundary — Catches unhandled JS errors in the component tree
 * and renders a graceful fallback UI instead of a white screen.
 *
 * Task: Week 9-10 / Frontend Polish (task.md line 537)
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[ErrorBoundary] Caught an error:', error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '300px',
          padding: '2rem',
          textAlign: 'center',
        }}>
          <div style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            background: 'rgba(239, 68, 68, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '1.5rem',
            border: '1px solid rgba(239, 68, 68, 0.2)',
          }}>
            <span style={{ fontSize: '28px' }}>⚠️</span>
          </div>
          <h3 style={{
            fontSize: '1.125rem',
            fontWeight: 600,
            color: '#e2e8f0',
            marginBottom: '0.5rem',
          }}>
            Something went wrong
          </h3>
          <p style={{
            fontSize: '0.875rem',
            color: '#94a3b8',
            maxWidth: '400px',
            marginBottom: '1.5rem',
            lineHeight: '1.6',
          }}>
            An unexpected error occurred. You can try again or refresh the page.
          </p>
          <button
            onClick={this.handleRetry}
            style={{
              padding: '0.625rem 1.5rem',
              background: '#6366f1',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '0.875rem',
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'background 0.2s',
            }}
            onMouseOver={(e) => (e.currentTarget.style.background = '#4f46e5')}
            onMouseOut={(e) => (e.currentTarget.style.background = '#6366f1')}
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
