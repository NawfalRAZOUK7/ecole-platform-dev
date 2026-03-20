/**
 * Admin Justification Review page — approve or deny absence justifications.
 *
 * Reference: Phase 4A — Admin Dashboard
 * Calls GET /admin/justifications, POST /attendance/justifications/{id}/review.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';
import { formatDate } from '@/shared/i18n';

interface Justification {
  id: string;
  attendance_record_id: string;
  parent_id: string;
  status: string;
  reason: string | null;
  rejection_reason: string | null;
  created_at: string | null;
}

export function JustificationReviewPage() {
  const { t, i18n } = useTranslation();
  const [items, setItems] = useState<Justification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [rejectionModal, setRejectionModal] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');

  const fetchJustifications = useCallback(async (cursor?: string) => {
    try {
      const params: Record<string, string | number | undefined> = {};
      if (cursor) params.cursor = cursor;
      if (statusFilter) params.status = statusFilter;

      const resp = await api.list<Justification>('/admin/justifications', params);
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
    fetchJustifications().finally(() => setLoading(false));
  }, [fetchJustifications]);

  async function handleApprove(justificationId: string) {
    setActionLoading(justificationId);
    try {
      await api.post(`/attendance/justifications/${justificationId}/review`, {
        decision: 'justified',
      });
      setItems((prev) => prev.map((j) =>
        j.id === justificationId ? { ...j, status: 'justified' } : j
      ));
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
    setActionLoading(null);
  }

  async function handleReject(justificationId: string) {
    if (!rejectionReason.trim()) return;
    setActionLoading(justificationId);
    try {
      await api.post(`/attendance/justifications/${justificationId}/review`, {
        decision: 'rejected',
        rejection_reason: rejectionReason,
      });
      setItems((prev) => prev.map((j) =>
        j.id === justificationId ? { ...j, status: 'rejected', rejection_reason: rejectionReason } : j
      ));
      setRejectionModal(null);
      setRejectionReason('');
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
    setActionLoading(null);
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'pending': return '#f59e0b';
      case 'justified': return '#10b981';
      case 'rejected': return '#ef4444';
      default: return '#6b7280';
    }
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('admin.justifications.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={() => fetchJustifications()} />

      <div className="filters-bar">
        <select
          className="filter-select"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
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
          {items.map((j) => (
            <div key={j.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                <span
                  className="status-badge"
                  style={{ color: getStatusColor(j.status), borderColor: getStatusColor(j.status) }}
                >
                  {t(`admin.justifications.status${j.status.charAt(0).toUpperCase() + j.status.slice(1)}`, j.status)}
                </span>
                <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
                  {formatDate(j.created_at, i18n.language)}
                </span>
              </div>

              <div style={{ marginBottom: 8 }}>
                <span style={{ fontWeight: 600, fontSize: 14 }}>{t('admin.justifications.reason')}:</span>
                <p style={{ margin: '4px 0', fontSize: 14, color: 'var(--color-text-secondary)' }}>
                  {j.reason || '-'}
                </p>
              </div>

              {j.rejection_reason && (
                <div style={{ marginBottom: 8, padding: 8, background: '#fef2f2', borderRadius: 'var(--radius)' }}>
                  <span style={{ fontWeight: 600, fontSize: 12, color: 'var(--color-danger)' }}>
                    {t('admin.justifications.rejectionReason')}:
                  </span>
                  <p style={{ margin: '4px 0', fontSize: 13 }}>{j.rejection_reason}</p>
                </div>
              )}

              {j.status === 'pending' && (
                <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={() => handleApprove(j.id)}
                    disabled={actionLoading === j.id}
                  >
                    {t('admin.justifications.approve')}
                  </button>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => {
                      setRejectionModal(j.id);
                      setRejectionReason('');
                    }}
                    disabled={actionLoading === j.id}
                  >
                    {t('admin.justifications.reject')}
                  </button>
                </div>
              )}

              {rejectionModal === j.id && (
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
                      onClick={() => handleReject(j.id)}
                      disabled={!rejectionReason.trim() || actionLoading === j.id}
                    >
                      {t('app.confirm')}
                    </button>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => setRejectionModal(null)}
                    >
                      {t('app.cancel')}
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {hasMore && (
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <button className="btn btn-secondary" onClick={() => fetchJustifications(nextCursor!)}>
            {t('feed.loadMore')}
          </button>
        </div>
      )}
    </div>
  );
}
