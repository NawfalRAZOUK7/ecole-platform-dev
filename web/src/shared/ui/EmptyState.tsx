/**
 * Empty state component — shown when a list has no items.
 * Uses Lucide icon with floating animation for visual polish.
 */

import { memo } from 'react';
import { useTranslation } from 'react-i18next';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  message?: string;
  icon?: React.ReactNode;
}

export const EmptyState = memo(function EmptyState({ message, icon }: EmptyStateProps) {
  const { t } = useTranslation();

  return (
    <div
      role="status"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 24px',
        color: 'var(--color-text-secondary)',
      }}
    >
      <span className="empty-state__icon" style={{ marginBottom: '16px' }}>
        {icon || <Inbox size={48} strokeWidth={1.2} color="var(--color-text-secondary)" />}
      </span>
      <p style={{ fontSize: '15px' }}>{message || t('app.empty')}</p>
    </div>
  );
});
