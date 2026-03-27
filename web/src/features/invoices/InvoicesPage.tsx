/**
 * Invoices page — invoice list with payment status, overdue indicators, retry.
 *
 * Reference: S-081 — Invoices page, Phase 12A — Extended with overdue + retry
 * Calls GET /invoices with cursor pagination. PAR and ADM roles.
 * Phase 12A: Overdue indicator (past due_date + pending), retry payment for failed.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
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

function isOverdue(inv: Invoice): boolean {
  if (inv.status !== 'pending') return false;
  return new Date(inv.due_date) < new Date();
}

export function InvoicesPage() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const isPar = user?.role === 'PAR';
  const [items, setItems] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [retrying, setRetrying] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');

  async function handleRetryPayment(invoiceId: string) {
    setRetrying(invoiceId);
    try {
      await api.post('/payments/initiate', {
        invoice_id: invoiceId,
        idempotency_key: `retry-${invoiceId}-${Date.now()}`,
      });
      await fetchInvoices();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setRetrying(null);
    }
  }

  const fetchInvoices = useCallback(async (cursor?: string) => {
    try {
      const params: Record<string, string | number | undefined> = {};
      if (cursor) params.cursor = cursor;
      if (statusFilter && statusFilter !== 'overdue') params.status = statusFilter;

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
  }, [t, statusFilter]);

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

  function getStatusColor(status: string, overdue?: boolean): string {
    if (overdue) return '#ef4444';
    switch (status) {
      case 'paid': return '#10b981';
      case 'pending': return '#f59e0b';
      case 'failed': return '#ef4444';
      case 'canceled': return '#6b7280';
      default: return '#6b7280';
    }
  }

  // Count overdue + client-side filter
  const overdueCount = items.filter(isOverdue).length;
  const displayedItems = statusFilter === 'overdue' ? items.filter(isOverdue) : items;

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('invoices.title')}</h1>

      {overdueCount > 0 && (
        <div className="invoice-overdue-banner">
          ⚠️ {t('invoices.overdueCount', { count: overdueCount })}
        </div>
      )}

      <div className="filters-bar">
        <div className="filter-pills">
          {[
            { value: '', label: t('invoices.allStatuses') },
            { value: 'pending', label: t('invoices.statusLabels.pending') },
            { value: 'paid', label: t('invoices.statusLabels.paid') },
            { value: 'failed', label: t('invoices.statusLabels.failed') },
          ].map((f) => (
            <button
              key={f.value}
              className={`filter-pill ${statusFilter === f.value ? 'filter-pill--active' : ''}`}
              onClick={() => setStatusFilter(f.value)}
            >
              {f.label}
              {f.value === '' && overdueCount > 0 ? '' : ''}
            </button>
          ))}
          {overdueCount > 0 && (
            <button
              className={`filter-pill filter-pill--danger ${statusFilter === 'overdue' ? 'filter-pill--active' : ''}`}
              onClick={() => setStatusFilter(statusFilter === 'overdue' ? '' : 'overdue')}
            >
              {t('invoices.overdue')} ({overdueCount})
            </button>
          )}
        </div>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={() => fetchInvoices()} />

      {displayedItems.length === 0 ? (
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
                  {isPar && <th>{t('invoices.actions')}</th>}
                </tr>
              </thead>
              <tbody>
                {displayedItems.map((inv) => {
                  const overdue = isOverdue(inv);
                  return (
                  <tr key={inv.id} className={overdue ? 'invoice-row--overdue' : ''}>
                    <td>{inv.label}</td>
                    <td>{formatCurrency(inv.total_cents / 100, inv.currency)}</td>
                    <td>
                      <span
                        className="status-badge"
                        style={{
                          color: getStatusColor(inv.status, overdue),
                          borderColor: getStatusColor(inv.status, overdue),
                        }}
                      >
                        {overdue ? t('invoices.overdue') : t(`invoices.statusLabels.${inv.status}`, inv.status)}
                      </span>
                    </td>
                    <td>{formatDate(inv.issued_date, i18n.language)}</td>
                    <td>
                      {formatDate(inv.due_date, i18n.language)}
                      {overdue && <span style={{ color: 'var(--color-danger)', fontSize: 12, marginInlineStart: 4 }}>⚠️</span>}
                    </td>
                    {isPar && (
                      <td>
                        {(inv.status === 'pending' || inv.status === 'failed') && (
                          <button
                            className="btn btn-sm btn-primary"
                            onClick={() => handleRetryPayment(inv.id)}
                            disabled={retrying === inv.id}
                          >
                            {retrying === inv.id ? '...' : inv.status === 'failed' ? t('invoices.retry') : t('invoices.pay')}
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                  );
                }
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
