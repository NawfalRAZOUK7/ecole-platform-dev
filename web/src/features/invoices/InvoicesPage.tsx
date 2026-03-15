/**
 * Invoices page — invoice list with payment status.
 *
 * Reference: S-081 — Invoices page
 * Calls GET /invoices with cursor pagination. PAR and ADM roles.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';
import { formatDate, formatCurrency } from '@/shared/i18n';

interface Invoice {
  id: string;
  school_id: string;
  student_id: string;
  year_id: string;
  label: string;
  total_cents: number;
  currency: string;
  status: string;
  issued_date: string;
  due_date: string;
  paid_at: string | null;
}

export function InvoicesPage() {
  const { t, i18n } = useTranslation();
  const [items, setItems] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  const fetchInvoices = useCallback(async (cursor?: string) => {
    try {
      const params: Record<string, string | number | undefined> = {};
      if (cursor) params.cursor = cursor;

      const resp = await api.list<Invoice>('/invoices', params);
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
  }, [t]);

  useEffect(() => {
    setLoading(true);
    fetchInvoices().finally(() => setLoading(false));
  }, [fetchInvoices]);

  async function handleLoadMore() {
    if (!nextCursor) return;
    setLoadingMore(true);
    await fetchInvoices(nextCursor);
    setLoadingMore(false);
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'paid': return '#10b981';
      case 'pending': return '#f59e0b';
      case 'failed': return '#ef4444';
      case 'canceled': return '#6b7280';
      default: return '#6b7280';
    }
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('invoices.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={() => fetchInvoices()} />

      {items.length === 0 ? (
        <EmptyState message={t('invoices.empty')} icon="💳" />
      ) : (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('invoices.items')}</th>
                  <th>{t('invoices.amount')}</th>
                  <th>{t('invoices.status')}</th>
                  <th>{t('invoices.issuedDate')}</th>
                  <th>{t('invoices.dueDate')}</th>
                </tr>
              </thead>
              <tbody>
                {items.map((inv) => (
                  <tr key={inv.id}>
                    <td>{inv.label}</td>
                    <td>{formatCurrency(inv.total_cents / 100, inv.currency)}</td>
                    <td>
                      <span
                        className="status-badge"
                        style={{
                          color: getStatusColor(inv.status),
                          borderColor: getStatusColor(inv.status),
                        }}
                      >
                        {t(`invoices.statusLabels.${inv.status}`, inv.status)}
                      </span>
                    </td>
                    <td>{formatDate(inv.issued_date, i18n.language)}</td>
                    <td>{formatDate(inv.due_date, i18n.language)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {hasMore && (
            <div style={{ textAlign: 'center', marginTop: '16px' }}>
              <button
                className="btn btn-secondary"
                onClick={handleLoadMore}
                disabled={loadingMore}
              >
                {loadingMore ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
