/**
 * Admin Audit Log page — searchable audit log with correlation_id filter and date range.
 *
 * Reference: Phase 4A — Admin Dashboard
 * Calls GET /admin/audit-logs with filters.
 */

import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { formatDate } from '@/shared/i18n';
import { useAdminAuditLogs } from './useAdmin';
import type { AuditEntry } from './admin.service';

export function AuditLogPage() {
  const { t, i18n } = useTranslation();
  const [correlationId, setCorrelationId] = useState('');
  const [actionType, setActionType] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const filters = useMemo(
    () => ({
      correlation_id: correlationId || undefined,
      action_type: actionType || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    }),
    [actionType, correlationId, dateFrom, dateTo]
  );
  const auditLogsQuery = useAdminAuditLogs(filters);
  const items: AuditEntry[] = useMemo(
    () => auditLogsQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [auditLogsQuery.data]
  );
  const dismissibleError = useDismissibleError(
    useMemo(() => toBannerError(auditLogsQuery.error, t('app.error')), [auditLogsQuery.error, t])
  );

  function getOutcomeColor(outcome: string): string {
    return outcome === 'success' ? 'var(--color-success)' : 'var(--color-error)';
  }

  if (auditLogsQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('admin.audit.title')}</h1>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void auditLogsQuery.refetch()}
      />

      <div className="filters-bar">
        <input
          type="text"
          className="filter-input"
          placeholder={t('admin.audit.correlationId')}
          value={correlationId}
          onChange={(e) => setCorrelationId(e.target.value)}
        />
        <input
          type="text"
          className="filter-input"
          placeholder={t('admin.audit.actionType')}
          value={actionType}
          onChange={(e) => setActionType(e.target.value)}
        />
        <input
          type="date"
          className="filter-input"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          title={t('admin.audit.dateFrom')}
        />
        <input
          type="date"
          className="filter-input"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          title={t('admin.audit.dateTo')}
        />
      </div>

      {items.length === 0 ? (
        <EmptyState message={t('admin.audit.empty')} icon="📋" />
      ) : (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('admin.audit.action')}</th>
                  <th>{t('admin.audit.outcome')}</th>
                  <th>{t('admin.audit.target')}</th>
                  <th>{t('admin.audit.ip')}</th>
                  <th>{t('admin.audit.date')}</th>
                  <th>{t('admin.audit.correlationId')}</th>
                </tr>
              </thead>
              <tbody>
                {items.map((log) => (
                  <tr key={log.id}>
                    <td>
                      <code style={{ fontSize: 12 }}>{log.action_type}</code>
                      {log.error_code && (
                        <span style={{ display: 'block', fontSize: 11, color: 'var(--color-danger)' }}>
                          {log.error_code}
                        </span>
                      )}
                    </td>
                    <td>
                      <span
                        className="status-badge"
                        style={{
                          color: getOutcomeColor(log.outcome),
                          borderColor: getOutcomeColor(log.outcome),
                        }}
                      >
                        {log.outcome}
                      </span>
                    </td>
                    <td>
                      {log.target_type && (
                        <span style={{ fontSize: 12 }}>
                          {log.target_type}
                          {log.target_id && <span style={{ color: 'var(--color-text-secondary)' }}> #{log.target_id.slice(0, 8)}</span>}
                        </span>
                      )}
                    </td>
                    <td style={{ fontSize: 12, fontFamily: 'monospace' }}>{log.ip_address || '-'}</td>
                    <td>{formatDate(log.created_at, i18n.language, { dateStyle: 'short', timeStyle: 'short' })}</td>
                    <td>
                      {log.correlation_id && (
                        <code style={{ fontSize: 11 }}>{log.correlation_id.slice(0, 8)}...</code>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {auditLogsQuery.hasNextPage && (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <button
                className="btn btn-secondary"
                onClick={() => void auditLogsQuery.fetchNextPage()}
                disabled={auditLogsQuery.isFetchingNextPage}
              >
                {auditLogsQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
