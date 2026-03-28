/**
 * Invoices page — invoice list with payment status, overdue indicators, retry.
 *
 * Reference: S-081 — Invoices page, Phase 12A — Extended with overdue + retry
 * Calls GET /invoices with cursor pagination. PAR and ADM roles.
 * Phase 12A: Overdue indicator (past due_date + pending), retry payment for failed.
 */

import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { formatDate, formatCurrency } from '@/shared/i18n';
import { useInitiateInvoicePayment, useInvoices } from './useInvoices';
import type { Invoice } from './invoices.service';

function isOverdue(invoice: Invoice): boolean {
  return invoice.status === 'pending' && new Date(invoice.due_date) < new Date();
}

export function InvoicesPage() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const isPar = user?.role === 'PAR';
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const invoicesQuery = useInvoices({
    status: statusFilter && statusFilter !== 'overdue' ? statusFilter : undefined,
  });
  const initiatePaymentMutation = useInitiateInvoicePayment();
  const items: Invoice[] = useMemo(
    () => invoicesQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [invoicesQuery.data]
  );
  const overdueCount = items.filter(isOverdue).length;
  const displayedItems = statusFilter === 'overdue' ? items.filter(isOverdue) : items;
  const dismissibleError = useDismissibleError(
    toBannerError(invoicesQuery.error ?? initiatePaymentMutation.error, t('app.error'))
  );

  async function handleRetryPayment(invoiceId: string) {
    setRetryingId(invoiceId);
    await initiatePaymentMutation.mutateAsync(invoiceId);
    await invoicesQuery.refetch();
    setRetryingId(null);
  }

  function getStatusColor(status: string, overdue?: boolean): string {
    if (overdue) return '#ef4444';
    switch (status) {
      case 'paid':
        return '#10b981';
      case 'pending':
        return '#f59e0b';
      case 'failed':
        return '#ef4444';
      case 'canceled':
        return '#6b7280';
      default:
        return '#6b7280';
    }
  }

  if (invoicesQuery.isLoading && !invoicesQuery.data) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('invoices.title')}</h1>

      {overdueCount > 0 && (
        <div className="invoice-overdue-banner">⚠️ {t('invoices.overdueCount', { count: overdueCount })}</div>
      )}

      <div className="filters-bar">
        <div className="filter-pills">
          {[
            { value: '', label: t('invoices.allStatuses') },
            { value: 'pending', label: t('invoices.statusLabels.pending') },
            { value: 'paid', label: t('invoices.statusLabels.paid') },
            { value: 'failed', label: t('invoices.statusLabels.failed') },
          ].map((filter) => (
            <button
              key={filter.value}
              className={`filter-pill ${statusFilter === filter.value ? 'filter-pill--active' : ''}`}
              onClick={() => setStatusFilter(filter.value)}
            >
              {filter.label}
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

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void invoicesQuery.refetch()}
      />

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
                {displayedItems.map((invoice) => {
                  const overdue = isOverdue(invoice);
                  return (
                    <tr key={invoice.id} className={overdue ? 'invoice-row--overdue' : ''}>
                      <td>{invoice.label}</td>
                      <td>{formatCurrency(invoice.total_cents / 100, invoice.currency)}</td>
                      <td>
                        <span className="status-badge" style={{ color: getStatusColor(invoice.status, overdue), borderColor: getStatusColor(invoice.status, overdue) }}>
                          {overdue ? t('invoices.overdue') : t(`invoices.statusLabels.${invoice.status}`, invoice.status)}
                        </span>
                      </td>
                      <td>{formatDate(invoice.issued_date, i18n.language)}</td>
                      <td>
                        {formatDate(invoice.due_date, i18n.language)}
                        {overdue && <span style={{ color: 'var(--color-danger)', fontSize: 12, marginInlineStart: 4 }}>⚠️</span>}
                      </td>
                      {isPar && (
                        <td>
                          {(invoice.status === 'pending' || invoice.status === 'failed') && (
                            <button
                              className="btn btn-sm btn-primary"
                              onClick={() => void handleRetryPayment(invoice.id)}
                              disabled={retryingId === invoice.id}
                            >
                              {retryingId === invoice.id ? '...' : invoice.status === 'failed' ? t('invoices.retry') : t('invoices.pay')}
                            </button>
                          )}
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {invoicesQuery.hasNextPage && (
            <div style={{ textAlign: 'center', marginTop: '16px' }}>
              <button className="btn btn-secondary" onClick={() => void invoicesQuery.fetchNextPage()} disabled={invoicesQuery.isFetchingNextPage}>
                {invoicesQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
