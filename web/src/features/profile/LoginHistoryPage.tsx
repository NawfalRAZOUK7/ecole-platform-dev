import { useTranslation } from 'react-i18next';
import { formatDate } from '@/shared/i18n';
import { Badge } from '@/shared/ui/Badge';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { useLoginHistory } from './useProfile';

export function LoginHistoryPage() {
  const { t } = useTranslation();
  const query = useLoginHistory();
  const entries = query.data ?? [];

  if (query.isLoading) return <LoadingState />;

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{t('loginHistory.title')}</h1>
        <p className="page-subtitle">{t('loginHistory.subtitle')}</p>
      </div>

      <ErrorBanner error={query.error instanceof Error ? query.error.message : null} onRetry={() => void query.refetch()} />

      {entries.length === 0 ? (
        <EmptyState message={t('loginHistory.empty')} />
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('loginHistory.date')}</th>
                <th>{t('loginHistory.ip')}</th>
                <th>{t('loginHistory.location')}</th>
                <th>{t('loginHistory.userAgent')}</th>
                <th>{t('loginHistory.status')}</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id}>
                  <td>{formatDate(entry.created_at)}</td>
                  <td>{entry.ip_address ?? '—'}</td>
                  <td>{entry.location ?? '—'}</td>
                  <td
                    style={{ maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                    title={entry.user_agent ?? undefined}
                  >
                    {entry.user_agent ?? '—'}
                  </td>
                  <td>
                    <Badge variant={entry.status === 'success' ? 'success' : 'error'}>
                      {t(`loginHistory.statuses.${entry.status}`)}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
