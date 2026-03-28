/**
 * Admin Users page — user list with search, filter, suspend/activate, role change.
 *
 * Reference: Phase 4A — Admin Dashboard
 * Calls GET /admin/users, PUT /admin/users/{id}/suspend, PUT /admin/users/{id}/activate, PUT /admin/users/{id}/role.
 */

import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { formatDate } from '@/shared/i18n';
import {
  useActivateAdminUser,
  useAdminUsers,
  useChangeAdminUserRole,
  useSuspendAdminUser,
} from './useAdmin';
import type { UserItem } from './admin.service';

export function UsersPage() {
  const { t, i18n } = useTranslation();
  const { user: currentUser } = useAuth();
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const filters = useMemo(
    () => ({
      search: search || undefined,
      role: roleFilter || undefined,
      status: statusFilter || undefined,
    }),
    [roleFilter, search, statusFilter]
  );
  const usersQuery = useAdminUsers(filters);
  const suspendUserMutation = useSuspendAdminUser();
  const activateUserMutation = useActivateAdminUser();
  const changeRoleMutation = useChangeAdminUserRole();

  const items: UserItem[] = useMemo(
    () => usersQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [usersQuery.data]
  );
  const dismissibleError = useDismissibleError(
    useMemo(
      () =>
        toBannerError(
          usersQuery.error ?? suspendUserMutation.error ?? activateUserMutation.error ?? changeRoleMutation.error,
          t('app.error')
        ),
      [activateUserMutation.error, changeRoleMutation.error, suspendUserMutation.error, t, usersQuery.error]
    )
  );

  async function handleSuspend(userId: string) {
    setActionLoading(userId);
    await suspendUserMutation.mutateAsync(userId);
    await usersQuery.refetch();
    setActionLoading(null);
  }

  async function handleActivate(userId: string) {
    setActionLoading(userId);
    await activateUserMutation.mutateAsync(userId);
    await usersQuery.refetch();
    setActionLoading(null);
  }

  async function handleRoleChange(userId: string, newRole: string) {
    setActionLoading(userId);
    await changeRoleMutation.mutateAsync({ userId, role: newRole });
    await usersQuery.refetch();
    setActionLoading(null);
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'active':
        return '#10b981';
      case 'suspended':
        return '#ef4444';
      case 'inactive':
        return '#6b7280';
      default:
        return '#6b7280';
    }
  }

  if (usersQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('admin.users.title')}</h1>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void usersQuery.refetch()}
      />

      <div className="filters-bar">
        <input
          type="text"
          className="filter-input"
          placeholder={t('admin.users.searchPlaceholder')}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select className="filter-select" value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
          <option value="">{t('admin.users.allRoles')}</option>
          <option value="ADM">{t('roles.ADM')}</option>
          <option value="DIR">{t('roles.DIR')}</option>
          <option value="TCH">{t('roles.TCH')}</option>
          <option value="PAR">{t('roles.PAR')}</option>
          <option value="STD">{t('roles.STD')}</option>
        </select>
        <select className="filter-select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">{t('admin.users.allStatuses')}</option>
          <option value="active">{t('admin.users.statusActive')}</option>
          <option value="suspended">{t('admin.users.statusSuspended')}</option>
          <option value="inactive">{t('admin.users.statusInactive')}</option>
        </select>
      </div>

      {items.length === 0 ? (
        <EmptyState message={t('admin.users.empty')} icon="👥" />
      ) : (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('admin.users.name')}</th>
                  <th>{t('admin.users.email')}</th>
                  <th>{t('admin.users.role')}</th>
                  <th>{t('admin.users.status')}</th>
                  <th>{t('admin.users.joined')}</th>
                  <th>{t('admin.users.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      {item.full_name}
                      {item.totp_enabled && <span title="2FA" style={{ marginInlineStart: 4 }}>🔐</span>}
                    </td>
                    <td>
                      {item.email}
                      {item.email_verified && <span title="Verified" style={{ marginInlineStart: 4 }}>✓</span>}
                    </td>
                    <td>
                      {currentUser?.role === 'ADM' && item.id !== currentUser.id ? (
                        <select
                          className="filter-select"
                          style={{ minWidth: 100 }}
                          value={item.role}
                          onChange={(e) => void handleRoleChange(item.id, e.target.value)}
                          disabled={actionLoading === item.id}
                        >
                          <option value="STD">{t('roles.STD')}</option>
                          <option value="PAR">{t('roles.PAR')}</option>
                          <option value="TCH">{t('roles.TCH')}</option>
                          <option value="DIR">{t('roles.DIR')}</option>
                        </select>
                      ) : (
                        <span className="role-badge">{t(`roles.${item.role}`, item.role)}</span>
                      )}
                    </td>
                    <td>
                      <span
                        className="status-badge"
                        style={{
                          color: getStatusColor(item.status),
                          borderColor: getStatusColor(item.status),
                        }}
                      >
                        {t(`admin.users.status${item.status.charAt(0).toUpperCase() + item.status.slice(1)}`, item.status)}
                      </span>
                    </td>
                    <td>{formatDate(item.created_at, i18n.language)}</td>
                    <td>
                      {currentUser?.role === 'ADM' && item.id !== currentUser.id && (
                        <>
                          {item.status === 'active' ? (
                            <button
                              className="btn btn-danger btn-sm"
                              onClick={() => void handleSuspend(item.id)}
                              disabled={actionLoading === item.id}
                            >
                              {t('admin.users.suspend')}
                            </button>
                          ) : item.status === 'suspended' ? (
                            <button
                              className="btn btn-primary btn-sm"
                              onClick={() => void handleActivate(item.id)}
                              disabled={actionLoading === item.id}
                            >
                              {t('admin.users.activate')}
                            </button>
                          ) : null}
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {usersQuery.hasNextPage && (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <button
                className="btn btn-secondary"
                onClick={() => void usersQuery.fetchNextPage()}
                disabled={usersQuery.isFetchingNextPage}
              >
                {usersQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
