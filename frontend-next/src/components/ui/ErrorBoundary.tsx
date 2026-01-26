'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, Bug, Copy, Check } from 'lucide-react';
import { t, type Language } from '@/lib/i18n';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  language?: Language;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  copied: boolean;
}

/**
 * Error Boundary component to catch JavaScript errors in child components
 * and display a fallback UI instead of crashing the whole application.
 * Supports Turkish, English, and German languages.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      copied: false,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo });
    
    // Log error to console in development
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Call optional error handler
    this.props.onError?.(error, errorInfo);

    // In production, you might want to send this to an error tracking service
    // Example: Sentry.captureException(error, { extra: errorInfo });
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  handleReload = (): void => {
    window.location.reload();
  };

  handleGoHome = (): void => {
    window.location.href = '/';
  };

  handleCopyError = (): void => {
    const errorText = `Error: ${this.state.error?.toString()}\n\nComponent Stack: ${this.state.errorInfo?.componentStack}`;
    navigator.clipboard.writeText(errorText);
    this.setState({ copied: true });
    setTimeout(() => this.setState({ copied: false }), 2000);
  };

  getLang(): Language {
    // Try to get language from props, localStorage, or default to 'tr'
    if (this.props.language) return this.props.language;
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('language');
      if (stored === 'en' || stored === 'de' || stored === 'tr') return stored;
    }
    return 'tr';
  }

  render(): ReactNode {
    const lang = this.getLang();
    
    if (this.state.hasError) {
      // Custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI with i18n support
      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center bg-gradient-to-br from-background to-muted/30">
          {/* Error Icon with Animation */}
          <div className="relative">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-red-500/20 to-orange-500/20 flex items-center justify-center mb-6 animate-pulse">
              <AlertTriangle className="w-10 h-10 text-red-500" />
            </div>
            <div className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-red-500 flex items-center justify-center">
              <Bug className="w-3 h-3 text-white" />
            </div>
          </div>
          
          <h2 className="text-2xl font-bold text-foreground mb-3">
            {t('errorOccurred', lang)}
          </h2>
          
          <p className="text-muted-foreground mb-6 max-w-md leading-relaxed">
            {t('unexpectedError', lang)}
          </p>

          {/* Error details in development */}
          {process.env.NODE_ENV === 'development' && this.state.error && (
            <details className="mb-6 text-left w-full max-w-2xl group">
              <summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-2">
                <Bug className="w-4 h-4" />
                {t('errorDetails', lang)} ({t('developerMode', lang)})
              </summary>
              <div className="mt-3 relative">
                <pre className="p-4 bg-muted/80 backdrop-blur-sm rounded-xl text-xs overflow-auto border border-border/50 max-h-64">
                  <code className="text-red-400">{this.state.error.toString()}</code>
                  <code className="text-muted-foreground">{this.state.errorInfo?.componentStack}</code>
                </pre>
                <button
                  onClick={this.handleCopyError}
                  className="absolute top-2 right-2 p-2 rounded-lg bg-background/80 hover:bg-accent transition-colors"
                  title={t('copyToClipboard', lang)}
                >
                  {this.state.copied ? (
                    <Check className="w-4 h-4 text-green-500" />
                  ) : (
                    <Copy className="w-4 h-4 text-muted-foreground" />
                  )}
                </button>
              </div>
            </details>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 flex-wrap justify-center">
            <button
              onClick={this.handleReset}
              className="flex items-center gap-2 px-5 py-2.5 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-all shadow-lg shadow-primary-500/25 hover:shadow-primary-500/40 hover:scale-105"
            >
              <RefreshCw className="w-4 h-4" />
              {t('retry', lang)}
            </button>
            
            <button
              onClick={this.handleReload}
              className="flex items-center gap-2 px-5 py-2.5 bg-muted hover:bg-accent rounded-xl transition-all hover:scale-105"
            >
              <RefreshCw className="w-4 h-4" />
              {t('reloadPage', lang)}
            </button>
            
            <button
              onClick={this.handleGoHome}
              className="flex items-center gap-2 px-5 py-2.5 bg-muted hover:bg-accent rounded-xl transition-all hover:scale-105"
            >
              <Home className="w-4 h-4" />
              {t('goHome', lang)}
            </button>
          </div>
          
          {/* Support Text */}
          <p className="text-xs text-muted-foreground mt-8">
            {lang === 'tr' && 'Sorun devam ederse lütfen sistem yöneticinize başvurun.'}
            {lang === 'en' && 'If the problem persists, please contact your system administrator.'}
            {lang === 'de' && 'Wenn das Problem weiterhin besteht, wenden Sie sich bitte an Ihren Systemadministrator.'}
          </p>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Higher-order component to wrap a component with ErrorBoundary
 */
export function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  fallback?: ReactNode
): React.FC<P> {
  const WithErrorBoundary: React.FC<P> = (props) => (
    <ErrorBoundary fallback={fallback}>
      <WrappedComponent {...props} />
    </ErrorBoundary>
  );

  WithErrorBoundary.displayName = `WithErrorBoundary(${WrappedComponent.displayName || WrappedComponent.name || 'Component'})`;

  return WithErrorBoundary;
}

/**
 * Custom hook to trigger error boundary
 * Useful for catching errors in event handlers and async operations
 */
export function useErrorHandler(): (error: Error) => void {
  const [, setError] = React.useState<Error | null>(null);

  return React.useCallback((error: Error) => {
    setError(() => {
      throw error;
    });
  }, []);
}
