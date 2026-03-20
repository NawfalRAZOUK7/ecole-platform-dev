/**
 * Admin Audit Log page — searchable audit log with correlation_id filter and date range.
 *
 * Reference: Phase 4A — Admin Dashboard
 * Calls GET /admin/audit-logs with filters.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';
import { formatDate } from '@/shared/i18n';

interface AuditEntry {
  id: string;
  action_type: string;
  outcome: string;
  actor_id: string | null;
  target_type: string | null;
  target_id: string | null;
  error_code: string | null;
  correlation_id: string | null;
  ip_address: string | null;
  created_at: string | null;
}

export function AuditLogPage() {
  const { t, i18n } = useTranslation();
  const [items, setItems] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [correlationId, setCorrelationId] = useState('');
  const [actionType, setActionType] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const fetchLogs = useCallback(async (cursor?: string) => {
    try {
      const params: Record<string, string | number | undefined> = {};
      if (cursor) params.cursor = cursor;
      if (correlationId) params.correlation_id = correlationId;
      if (actionType) params.action_type = actionType;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;

      const resp = await api.list<AuditEntry>('/admin/audit-logs', params);
      if (cursor) {
        setItems((prev) => [...prev, ...resp.data]);
      } else {
        setItems(resp.data);
      }
      setNextCursor(resp.meta.next_cursor);
      setHasMore(resp.meta.has_more);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [t, correlationId, actionType, dateFrom, dateTo]);

  useEffect(() => {
    setLoading(true);
    fetchLogs().finally(() => setLoading(false));
  }, [fetchLogs]);

  async function handleLoadMore() {
    if (!nextCursor) return;
    setLoadingMore(true);
    await fetchLogs(nextCursor);
    setLoadingMore(false);
  }

  function getOutcomeColor(outcome: string): string {
    return outcome === 'success' ? '#10b981' : '#ef4444';
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('admin.audit.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={() => fetchLogs()} />

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

          {hasMore && (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <button className="btn btn-secondary" onClick={handleLoadMore} disabled={loadingMore}>
                {loadingMore ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
