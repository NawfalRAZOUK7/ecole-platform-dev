/**
 * Admin Justification Review page — approve or deny absence justifications.
 *
 * Reference: Phase 4A — Admin Dashboard
 * Calls GET /admin/justifications, POST /attendance/justifications/{id}/review.
 */

import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { formatDate } from '@/shared/i18n';
import { useAdminJustifications, useReviewJustification } from './useAdmin';
import type { Justification } from './admin.service';

export function JustificationReviewPage() {
  const { t, i18n } = useTranslation();
  const [statusFilter, setStatusFilter] = useState('pending');
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [rejectionModal, setRejectionModal] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');

  const justificationsQuery = useAdminJustifications({
    status: statusFilter || undefined,
  });
  const reviewMutation = useReviewJustification();
  const items: Justification[] = useMemo(
    () => justificationsQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [justificationsQuery.data]
  );
  const dismissibleError = useDismissibleError(
    useMemo(
      () => toBannerError(justificationsQuery.error ?? reviewMutation.error, t('app.error')),
      [justificationsQuery.error, reviewMutation.error, t]
    )
  );

  async function handleApprove(justificationId: string) {
    setActionLoading(justificationId);
    await reviewMutation.mutateAsync({
      justificationId,
      decision: 'justified',
    });
    await justificationsQuery.refetch();
    setActionLoading(null);
  }

  async function handleReject(justificationId: string) {
    if (!rejectionReason.trim()) return;
    setActionLoading(justificationId);
    await reviewMutation.mutateAsync({
      justificationId,
      decision: 'rejected',
      rejectionReason,
    });
    await justificationsQuery.refetch();
    setRejectionModal(null);
    setRejectionReason('');
    setActionLoading(null);
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'pending':
        return 'var(--color-warning)';
      case 'justified':
        return 'var(--color-success)';
      case 'rejected':
        return 'var(--color-error)';
      default:
        return 'var(--color-text-secondary)';
    }
  }

  if (justificationsQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('admin.justifications.title')}</h1>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void justificationsQuery.refetch()}
      />

      <div className="filters-bar">
        <select className="filter-select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="pending">{t('admin.justifications.statusPending')}</option>
          <option value="justified">{t('admin.justifications.statusJustified')}</option>
          <option value="rejected">{t('admin.justifications.statusRejected')}</option>
          <option value="">{t('admin.justifications.allStatuses')}</option>
        </select>
      </div>

      {items.length === 0 ? (
        <EmptyState message={t('admin.justifications.empty')} icon="✅" />
      ) : (
        <div className="card-list">
          {items.map((item) => (
            <div key={item.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                <span
                  className="status-badge"
                  style={{ color: getStatusColor(item.status), borderColor: getStatusColor(item.status) }}
                >
                  {t(`admin.justifications.status${item.status.charAt(0).toUpperCase() + item.status.slice(1)}`, item.status)}
                </span>
                <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
                  {formatDate(item.created_at, i18n.language)}
                </span>
              </div>

              <div style={{ marginBottom: 8 }}>
                <span style={{ fontWeight: 600, fontSize: 14 }}>{t('admin.justifications.reason')}:</span>
                <p style={{ margin: '4px 0', fontSize: 14, color: 'var(--color-text-secondary)' }}>
                  {item.reason || '-'}
                </p>
              </div>

              {item.rejection_reason && (
                <div style={{ marginBottom: 8, padding: 8, background: 'var(--color-surface-error)', borderRadius: 'var(--radius)' }}>
                  <span style={{ fontWeight: 600, fontSize: 12, color: 'var(--color-danger)' }}>
                    {t('admin.justifications.rejectionReason')}:
                  </span>
                  <p style={{ margin: '4px 0', fontSize: 13 }}>{item.rejection_reason}</p>
                </div>
              )}

              {item.status === 'pending' && (
                <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={() => void handleApprove(item.id)}
                    disabled={actionLoading === item.id}
                  >
                    {t('admin.justifications.approve')}
                  </button>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => {
                      setRejectionModal(item.id);
                      setRejectionReason('');
                    }}
                    disabled={actionLoading === item.id}
                  >
                    {t('admin.justifications.reject')}
                  </button>
                </div>
              )}

              {rejectionModal === item.id && (
                <div style={{ marginTop: 12, padding: 12, background: 'var(--color-bg)', borderRadius: 'var(--radius)' }}>
                  <div className="form-field">
                    <label>{t('admin.justifications.rejectionReason')}</label>
                    <input
                      type="text"
                      value={rejectionReason}
                      onChange={(e) => setRejectionReason(e.target.value)}
                      placeholder={t('admin.justifications.rejectionPlaceholder')}
                    />
                  </div>
                  <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => void handleReject(item.id)}
                      disabled={!rejectionReason.trim() || actionLoading === item.id}
                    >
                      {t('app.confirm')}
                    </button>
                    <button className="btn btn-secondary btn-sm" onClick={() => setRejectionModal(null)}>
                      {t('app.cancel')}
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {justificationsQuery.hasNextPage && (
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <button
            className="btn btn-secondary"
            onClick={() => void justificationsQuery.fetchNextPage()}
            disabled={justificationsQuery.isFetchingNextPage}
          >
            {justificationsQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
          </button>
        </div>
      )}
    </div>
  );
}
