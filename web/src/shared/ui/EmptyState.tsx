/**
 * Empty state component — shown when a list has no items.
 */

import { useTranslation } from 'react-i18next';

interface EmptyStateProps {
  message?: string;
  icon?: string;
}

export function EmptyState({ message, icon = '📭' }: EmptyStateProps) {
  const { t } = useTranslation();

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 24px',
        color: '#9ca3af',
      }}
    >
      <span style={{ fontSize: '48px', marginBottom: '16px' }}>{icon}</span>
      <p style={{ fontSize: '15px' }}>{message || t('app.empty')}</p>
    </div>
  );
}
