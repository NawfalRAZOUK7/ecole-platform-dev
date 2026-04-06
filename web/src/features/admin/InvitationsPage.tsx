/**
 * Admin Invitations page — create, list, and revoke invitation codes.
 *
 * Reference: Phase 4A — Admin Dashboard
 * Calls GET /admin/invitations, POST /invites/create, POST /invites/revoke.
 */

import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { formatDate } from '@/shared/i18n';
import {
  useAdminInvitations,
  useAdminUserSearch,
  useCreateInvitation,
  useRevokeInvitation,
} from './useAdmin';
import type { Invitation, UserItem } from './admin.service';

export function InvitationsPage() {
  const { t, i18n } = useTranslation();
  const [statusFilter, setStatusFilter] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [createRole, setCreateRole] = useState('STD');
  const [createHours, setCreateHours] = useState(48);
  const [createdCode, setCreatedCode] = useState<string | null>(null);
  const [revoking, setRevoking] = useState<string | null>(null);
  const [targetStudentSearch, setTargetStudentSearch] = useState('');
  const [studentSearchQuery, setStudentSearchQuery] = useState('');
  const [selectedTargetStudent, setSelectedTargetStudent] = useState<UserItem | null>(null);

  const invitationsQuery = useAdminInvitations({
    status: statusFilter || undefined,
  });
  const createInvitationMutation = useCreateInvitation();
  const revokeInvitationMutation = useRevokeInvitation();
  const targetStudentQuery = useAdminUserSearch(
    createRole === 'PAR' ? studentSearchQuery : '',
    'STD'
  );

  const items: Invitation[] = useMemo(
    () => invitationsQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [invitationsQuery.data]
  );
  const targetStudentResults = targetStudentQuery.data ?? [];
  const dismissibleError = useDismissibleError(
    useMemo(
      () =>
        toBannerError(
          invitationsQuery.error ?? createInvitationMutation.error ?? revokeInvitationMutation.error,
          t('app.error')
        ),
      [createInvitationMutation.error, invitationsQuery.error, revokeInvitationMutation.error, t]
    )
  );

  useEffect(() => {
    if (createRole !== 'PAR' || targetStudentSearch.length < 2) {
      setStudentSearchQuery('');
      return;
    }
    const timer = window.setTimeout(() => {
      setStudentSearchQuery(targetStudentSearch);
    }, 300);
    return () => window.clearTimeout(timer);
  }, [createRole, targetStudentSearch]);

  useEffect(() => {
    if (createRole !== 'PAR') {
      setSelectedTargetStudent(null);
      setTargetStudentSearch('');
      setStudentSearchQuery('');
    }
  }, [createRole]);

  async function handleCreate() {
    setCreatedCode(null);
    const response = await createInvitationMutation.mutateAsync({
      role_target: createRole,
      expires_in_hours: createHours,
      target_student_id: createRole === 'PAR' && selectedTargetStudent ? selectedTargetStudent.id : undefined,
    });
    setCreatedCode(response.code);
    setSelectedTargetStudent(null);
    setTargetStudentSearch('');
    setStudentSearchQuery('');
    await invitationsQuery.refetch();
  }

  async function handleRevoke(inviteId: string) {
    setRevoking(inviteId);
    await revokeInvitationMutation.mutateAsync(inviteId);
    await invitationsQuery.refetch();
    setRevoking(null);
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'active':
        return 'var(--color-success)';
      case 'consumed':
        return 'var(--color-primary)';
      case 'expired':
        return 'var(--color-text-secondary)';
      default:
        return 'var(--color-text-secondary)';
    }
  }

  if (invitationsQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>{t('admin.invitations.title')}</h1>
        <button className="btn btn-primary" onClick={() => setShowCreate(!showCreate)}>
          {t('admin.invitations.create')}
        </button>
      </div>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void invitationsQuery.refetch()}
      />

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
            <button className="btn btn-primary" onClick={() => void handleCreate()} disabled={createInvitationMutation.isPending}>
              {createInvitationMutation.isPending ? t('app.loading') : t('admin.invitations.generate')}
            </button>
          </div>

          {createRole === 'PAR' && (
            <div style={{ marginTop: 12 }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 500, marginBottom: 4, color: 'var(--color-text-secondary)' }}>
                {t('admin.invitations.prelinkStudent')}
              </label>
              {selectedTargetStudent ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 10px', background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', fontSize: 13 }}>
                  <span>{selectedTargetStudent.full_name} ({selectedTargetStudent.email})</span>
                  <button
                    className="btn btn-sm"
                    onClick={() => { setSelectedTargetStudent(null); setTargetStudentSearch(''); }}
                    style={{ marginLeft: 'auto', fontSize: 11, padding: '2px 6px' }}
                  >
                    &times;
                  </button>
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
                  {targetStudentQuery.isFetching && (
                    <span style={{ position: 'absolute', right: 8, top: 8, fontSize: 12 }}>{t('app.loading')}</span>
                  )}
                  {targetStudentResults.length > 0 && (
                    <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', maxHeight: 180, overflowY: 'auto', zIndex: 10 }}>
                      {targetStudentResults.map((user) => (
                        <div
                          key={user.id}
                          onClick={() => { setSelectedTargetStudent(user); setTargetStudentSearch(''); setStudentSearchQuery(''); }}
                          style={{ padding: '6px 10px', cursor: 'pointer', fontSize: 13, borderBottom: '1px solid var(--color-border)' }}
                          onMouseOver={(event) => { event.currentTarget.style.background = 'var(--color-surface)'; }}
                          onMouseOut={(event) => { event.currentTarget.style.background = 'transparent'; }}
                        >
                          {user.full_name} — {user.email}
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
                {items.map((item) => (
                  <tr key={item.id}>
                    <td><span className="role-badge">{t(`roles.${item.role_target}`, item.role_target)}</span></td>
                    <td>
                      <span
                        className="status-badge"
                        style={{ color: getStatusColor(item.status), borderColor: getStatusColor(item.status) }}
                      >
                        {t(`admin.invitations.status${item.status.charAt(0).toUpperCase() + item.status.slice(1)}`, item.status)}
                      </span>
                    </td>
                    <td>{formatDate(item.expires_at, i18n.language)}</td>
                    <td>{formatDate(item.created_at, i18n.language)}</td>
                    <td>
                      {item.status === 'active' && (
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => void handleRevoke(item.id)}
                          disabled={revoking === item.id}
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

          {invitationsQuery.hasNextPage && (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <button
                className="btn btn-secondary"
                onClick={() => void invitationsQuery.fetchNextPage()}
                disabled={invitationsQuery.isFetchingNextPage}
              >
                {invitationsQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
