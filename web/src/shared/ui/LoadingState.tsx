/**
 * Loading state component — spinner with message.
 */

import { useTranslation } from 'react-i18next';

interface LoadingStateProps {
  message?: string;
}

export function LoadingState({ message }: LoadingStateProps) {
  const { t } = useTranslation();

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 24px',
        color: '#6b7280',
      }}
    >
      <div className="spinner" />
      <p style={{ marginTop: '16px', fontSize: '14px' }}>{message || t('app.loading')}</p>
    </div>
  );
}
