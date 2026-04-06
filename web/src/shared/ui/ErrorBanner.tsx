/**
 * Categorized error banner component.
 *
 * Reference: S-085 — Error handling with categorized banners
 * Displays API errors by category with appropriate styling.
 * Dismissible + retry button for retryable errors.
 */

import { useTranslation } from 'react-i18next';
import type { ApiError } from '@/services/api/client';

interface ErrorBannerProps {
  error: ApiError | string | null;
  onDismiss?: () => void;
  onRetry?: () => void;
}

const CATEGORY_STYLES: Record<string, { bg: string; border: string; icon: string }> = {
  validation: { bg: '#fff3cd', border: '#ffc107', icon: '!' },
  authn: { bg: '#f8d7da', border: '#dc3545', icon: '🔒' },
  authz: { bg: '#f8d7da', border: '#dc3545', icon: '🚫' },
  conflict: { bg: '#fff3cd', border: '#ffc107', icon: '⚠' },
  system: { bg: '#f8d7da', border: '#dc3545', icon: '⚙' },
  rate_limit: { bg: '#fff3cd', border: '#ffc107', icon: '⏱' },
  not_found: { bg: '#cce5ff', border: '#0d6efd', icon: '?' },
  network: { bg: '#f8d7da', border: '#dc3545', icon: '📡' },
};

export function ErrorBanner({ error, onDismiss, onRetry }: ErrorBannerProps) {
  const { t } = useTranslation();

  if (!error) return null;

  const isApiError = typeof error !== 'string';
  const category = isApiError ? error.category : 'system';
  const message = isApiError ? error.message : error;
  const retryable = isApiError ? error.retryable : false;
  const style = CATEGORY_STYLES[category] || CATEGORY_STYLES.system;
  const categoryLabel = t(`errors.${category}`, t('errors.unknown'));

  return (
    <div
      role="alert"
      aria-live="assertive"
      style={{
        padding: '12px 16px',
        marginBottom: '16px',
        borderRadius: '8px',
        backgroundColor: style.bg,
        borderLeft: `4px solid ${style.border}`,
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
      }}
    >
      <span style={{ fontSize: '18px' }}>{style.icon}</span>
      <div style={{ flex: 1 }}>
        <strong style={{ display: 'block', marginBottom: '2px', fontSize: '13px', opacity: 0.7 }}>
          {categoryLabel}
        </strong>
        <span>{message}</span>
      </div>
      {retryable && onRetry && (
        <button
          onClick={onRetry}
          style={{
            padding: '6px 12px',
            borderRadius: '4px',
            border: `1px solid ${style.border}`,
            background: 'transparent',
            cursor: 'pointer',
            fontSize: '13px',
          }}
        >
          {t('app.retry')}
        </button>
      )}
      {onDismiss && (
        <button
          onClick={onDismiss}
          aria-label={t('app.close')}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontSize: '18px',
            padding: '0 4px',
            opacity: 0.6,
          }}
        >
          ×
        </button>
      )}
    </div>
  );
}
