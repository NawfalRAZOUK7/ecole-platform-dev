import { useTranslation } from 'react-i18next';

interface RetryButtonProps {
  onRetry: () => void;
  loading?: boolean;
}

export function RetryButton({ onRetry, loading = false }: RetryButtonProps) {
  const { t } = useTranslation();

  return (
    <button
      type="button"
      className="retry-button"
      onClick={onRetry}
      disabled={loading}
      aria-busy={loading}
    >
      <span aria-hidden="true">{loading ? '⟳' : '↻'}</span>
      <span>{t('app.retry', { defaultValue: 'Retry' })}</span>
    </button>
  );
}
