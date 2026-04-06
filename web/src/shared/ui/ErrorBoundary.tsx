import { Component, type ErrorInfo, type ReactNode } from 'react';
import i18next from '@/shared/i18n';

interface ErrorBoundaryProps {
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  public state: ErrorBoundaryState = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error,
    };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.props.onError?.(error, errorInfo);
  }

  private reset = () => {
    this.setState({
      hasError: false,
      error: null,
    });
  };

  public render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    if (this.props.fallback) {
      return this.props.fallback;
    }

    return (
      <div className="error-boundary">
        <div className="error-boundary__card">
          <span aria-hidden="true">⚠️</span>
          <h2>{i18next.t('errors.boundaryTitle', { defaultValue: 'Something went wrong' })}</h2>
          <p>
            {this.state.error?.message
              || i18next.t('errors.boundaryMessage', { defaultValue: 'An unexpected error occurred.' })}
          </p>
          <div className="error-boundary__actions">
            <button type="button" className="btn btn-primary" onClick={this.reset}>
              {i18next.t('app.retry', { defaultValue: 'Try Again' })}
            </button>
            <a href="/" className="btn btn-secondary">
              {i18next.t('nav.home', { defaultValue: 'Home' })}
            </a>
          </div>
        </div>
      </div>
    );
  }
}
