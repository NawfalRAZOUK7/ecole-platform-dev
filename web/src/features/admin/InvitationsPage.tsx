/**
 * Admin Invitations page — create, list, and revoke invitation codes.
 *
 * Reference: Phase 4A — Admin Dashboard
 * Calls GET /admin/invitations, POST /invites/create, POST /invites/revoke.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';
import { formatDate } from '@/shared/i18n';

interface Invitation {
  id: string;
  role_target: string;
  consumed_at: string | null;
  consumed_by: string | null;
  expires_at: string;
  created_at: string | null;
  issuer_user_id: string | null;
  status: string;
}

export function InvitationsPage() {
  const { t, i18n } = useTranslation();
  const [items, setItems] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [createRole, setCreateRole] = useState('STD');
  const [createHours, setCreateHours] = useState(48);
  const [creating, setCreating] = useState(false);
  const [createdCode, setCreatedCode] = useState<string | null>(null);
  const [revoking, setRevoking] = useState<string | null>(null);

  // Phase 4D-patch: target student for PAR invitations
  const [targetStudentSearch, setTargetStudentSearch] = useState('');
  const [targetStudentResults, setTargetStudentResults] = useState<{ id: string; full_name: string; email: string }[]>([]);
  const [selectedTargetStudent, setSelectedTargetStudent] = useState<{ id: string; full_name: string; email: string } | null>(null);

  const fetchInvitations = useCallback(async (cursor?: string) => {
    try {
      const params: Record<string, string | number | undefined> = {};
      if (cursor) params.cursor = cursor;
      if (statusFilter) params.status = statusFilter;

      const resp = await api.list<Invitation>('/admin/invitations', params);
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
    fetchInvitations().finally(() => setLoading(false));
  }, [fetchInvitations]);

  // Phase 4D-patch: search students for pre-link when role=PAR
  useEffect(() => {
    if (createRole !== 'PAR' || targetStudentSearch.length < 2) {
      setTargetStudentResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const resp = await api.list<{ id: string; full_name: string; email: string }>('/admin/users', {
          search: targetStudentSearch,
          role: 'STD',
        });
        setTargetStudentResults(resp.data);
      } catch { /* ignore */ }
    }, 300);
    return () => clearTimeout(timer);
  }, [targetStudentSearch, createRole]);

  // Clear target student when role changes away from PAR
  useEffect(() => {
    if (createRole !== 'PAR') {
      setSelectedTargetStudent(null);
      setTargetStudentSearch('');
    }
  }, [createRole]);

  async function handleCreate() {
    setCreating(true);
    setCreatedCode(null);
    try {
      const body: Record<string, unknown> = {
        role_target: createRole,
        expires_in_hours: createHours,
      };
      if (createRole === 'PAR' && selectedTargetStudent) {
        body.target_student_id = selectedTargetStudent.id;
      }
      const resp = await api.post<{ code: string }>('/invites/create', body);
      setCreatedCode(resp.data.code);
      setSelectedTargetStudent(null);
      setTargetStudentSearch('');
      fetchInvitations();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
    setCreating(false);
  }

  async function handleRevoke(inviteId: string) {
    setRevoking(inviteId);
    try {
      await api.post('/invites/revoke', { invite_id: inviteId });
      setItems((prev) => prev.map((inv) =>
        inv.id === inviteId ? { ...inv, status: 'expired' } : inv
      ));
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
    setRevoking(null);
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'active': return '#10b981';
      case 'consumed': return '#2563eb';
      case 'expired': return '#6b7280';
      default: return '#6b7280';
    }
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>{t('admin.invitations.title')}</h1>
        <button className="btn btn-primary" onClick={() => setShowCreate(!showCreate)}>
          {t('admin.invitations.create')}
        </button>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={() => fetchInvitations()} />

      {showCreate && (
        <div className="card" style={{ marginBottom: 20 }}>
          <h3 style={{ marginBottom: 12, fontSize: 15, fontWeight: 600 }}>{t('admin.invitations.createNew')}</h3>
          <div className="filters-bar">
            <select className="filter-select" value={createRole} onChange={(e) => setCreateRole(e.target.value)}>
              <option value="STD">{t('roles.STD')}</option>
              <option value="PAR">{t('roles.PAR')}</option>
              <option value="TCH">{t('roles.TCH')}</option>
              <option value="DIR">{t('roles.DIR')}</option>
            </select>
            <select className="filter-select" value={createHours} onChange={(e) => setCreateHours(Number(e.target.value))}>
              <option value={24}>24h</option>
              <option value={48}>48h</option>
              <option value={72}>72h</option>
              <option value={168}>7 {t('admin.invitations.days')}</option>
            </select>
            <button className="btn btn-primary" onClick={handleCreate} disabled={creating}>
              {creating ? t('app.loading') : t('admin.invitations.generate')}
            </button>
          </div>
          {/* Phase 4D-patch: Pre-link to student when role=PAR */}
          {createRole === 'PAR' && (
            <div style={{ marginTop: 12 }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 500, marginBottom: 4, color: 'var(--color-text-secondary)' }}>
                {t('admin.invitations.prelinkStudent')}
              </label>
              {selectedTargetStudent ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 10px', background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', fontSize: 13 }}>
                  <span>{selectedTargetStudent.full_name} ({selectedTargetStudent.email})</span>
                  <button className="btn btn-sm" onClick={() => { setSelectedTargetStudent(null); setTargetStudentSearch(''); }} style={{ marginLeft: 'auto', fontSize: 11, padding: '2px 6px' }}>&times;</button>
                </div>
              ) : (
                <div style={{ position: 'relative' }}>
                  <input
                    type="text"
                    className="filter-input"
                    placeholder={t('admin.invitations.searchStudent')}
                    value={targetStudentSearch}
                    onChange={(e) => setTargetStudentSearch(e.target.value)}
                    style={{ width: '100%' }}
                  />
                  {targetStudentResults.length > 0 && (
                    <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', maxHeight: 180, overflowY: 'auto', zIndex: 10 }}>
                      {targetStudentResults.map((u) => (
                        <div
                          key={u.id}
                          onClick={() => { setSelectedTargetStudent(u); setTargetStudentResults([]); setTargetStudentSearch(''); }}
                          style={{ padding: '6px 10px', cursor: 'pointer', fontSize: 13, borderBottom: '1px solid var(--color-border)' }}
                          onMouseOver={(e) => (e.currentTarget.style.background = 'var(--color-surface)')}
                          onMouseOut={(e) => (e.currentTarget.style.background = 'transparent')}
                        >
                          {u.full_name} — {u.email}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
          {createdCode && (
            <div className="code-display">
              <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>{t('admin.invitations.codeLabel')}</span>
              <code className="invite-code">{createdCode}</code>
            </div>
          )}
        </div>
      )}

      <div className="filters-bar">
        <select className="filter-select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">{t('admin.invitations.allStatuses')}</option>
          <option value="active">{t('admin.invitations.statusActive')}</option>
          <option value="consumed">{t('admin.invitations.statusConsumed')}</option>
          <option value="expired">{t('admin.invitations.statusExpired')}</option>
        </select>
      </div>

      {items.length === 0 ? (
        <EmptyState message={t('admin.invitations.empty')} icon="🎟️" />
      ) : (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('admin.invitations.targetRole')}</th>
                  <th>{t('admin.invitations.status')}</th>
                  <th>{t('admin.invitations.expiresAt')}</th>
                  <th>{t('admin.invitations.createdAt')}</th>
                  <th>{t('admin.users.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {items.map((inv) => (
                  <tr key={inv.id}>
                    <td><span className="role-badge">{t(`roles.${inv.role_target}`, inv.role_target)}</span></td>
                    <td>
                      <span
                        className="status-badge"
                        style={{ color: getStatusColor(inv.status), borderColor: getStatusColor(inv.status) }}
                      >
                        {t(`admin.invitations.status${inv.status.charAt(0).toUpperCase() + inv.status.slice(1)}`, inv.status)}
                      </span>
                    </td>
                    <td>{formatDate(inv.expires_at, i18n.language)}</td>
                    <td>{formatDate(inv.created_at, i18n.language)}</td>
                    <td>
                      {inv.status === 'active' && (
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => handleRevoke(inv.id)}
                          disabled={revoking === inv.id}
                        >
                          {t('admin.invitations.revoke')}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {hasMore && (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <button className="btn btn-secondary" onClick={() => fetchInvitations(nextCursor!)}>
                {t('feed.loadMore')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
