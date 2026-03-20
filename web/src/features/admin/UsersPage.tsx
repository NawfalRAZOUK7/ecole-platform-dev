/**
 * Admin Users page — user list with search, filter, suspend/activate, role change.
 *
 * Reference: Phase 4A — Admin Dashboard
 * Calls GET /admin/users, PUT /admin/users/{id}/suspend, PUT /admin/users/{id}/activate, PUT /admin/users/{id}/role.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { useAuth } from '@/services/auth/AuthContext';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';
import { formatDate } from '@/shared/i18n';

interface UserItem {
  id: string;
  email: string;
  full_name: string;
  status: string;
  role: string;
  created_at: string | null;
  email_verified: boolean;
  totp_enabled: boolean;
}

export function UsersPage() {
  const { t, i18n } = useTranslation();
  const { user: currentUser } = useAuth();
  const [items, setItems] = useState<UserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchUsers = useCallback(async (cursor?: string) => {
    try {
      const params: Record<string, string | number | undefined> = {};
      if (cursor) params.cursor = cursor;
      if (search) params.search = search;
      if (roleFilter) params.role = roleFilter;
      if (statusFilter) params.status = statusFilter;

      const resp = await api.list<UserItem>('/admin/users', params);
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
  }, [t, search, roleFilter, statusFilter]);

  useEffect(() => {
    setLoading(true);
    fetchUsers().finally(() => setLoading(false));
  }, [fetchUsers]);

  async function handleLoadMore() {
    if (!nextCursor) return;
    setLoadingMore(true);
    await fetchUsers(nextCursor);
    setLoadingMore(false);
  }

  async function handleSuspend(userId: string) {
    setActionLoading(userId);
    try {
      await api.put(`/admin/users/${userId}/suspend`);
      setItems((prev) => prev.map((u) => u.id === userId ? { ...u, status: 'suspended' } : u));
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
    setActionLoading(null);
  }

  async function handleActivate(userId: string) {
    setActionLoading(userId);
    try {
      await api.put(`/admin/users/${userId}/activate`);
      setItems((prev) => prev.map((u) => u.id === userId ? { ...u, status: 'active' } : u));
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
    setActionLoading(null);
  }

  async function handleRoleChange(userId: string, newRole: string) {
    setActionLoading(userId);
    try {
      await api.put(`/admin/users/${userId}/role`, undefined);
      // The API uses a query param for role — use raw request
      const resp = await fetch(`/api/v1/admin/users/${userId}/role?role=${newRole}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${(await import('@/services/api/client')).getAccessToken()}`,
          'Accept': 'application/json',
        },
        credentials: 'include',
      });
      if (resp.ok) {
        setItems((prev) => prev.map((u) => u.id === userId ? { ...u, role: newRole } : u));
      }
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
    setActionLoading(null);
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'active': return '#10b981';
      case 'suspended': return '#ef4444';
      case 'inactive': return '#6b7280';
      default: return '#6b7280';
    }
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('admin.users.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={() => fetchUsers()} />

      <div className="filters-bar">
        <input
          type="text"
          className="filter-input"
          placeholder={t('admin.users.searchPlaceholder')}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="filter-select"
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
        >
          <option value="">{t('admin.users.allRoles')}</option>
          <option value="ADM">{t('roles.ADM')}</option>
          <option value="DIR">{t('roles.DIR')}</option>
          <option value="TCH">{t('roles.TCH')}</option>
          <option value="PAR">{t('roles.PAR')}</option>
          <option value="STD">{t('roles.STD')}</option>
        </select>
        <select
          className="filter-select"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
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
                {items.map((u) => (
                  <tr key={u.id}>
                    <td>
                      {u.full_name}
                      {u.totp_enabled && <span title="2FA" style={{ marginInlineStart: 4 }}>🔐</span>}
                    </td>
                    <td>
                      {u.email}
                      {u.email_verified && <span title="Verified" style={{ marginInlineStart: 4 }}>✓</span>}
                    </td>
                    <td>
                      {currentUser?.role === 'ADM' && u.id !== currentUser?.id ? (
                        <select
                          className="filter-select"
                          style={{ minWidth: 100 }}
                          value={u.role}
                          onChange={(e) => handleRoleChange(u.id, e.target.value)}
                          disabled={actionLoading === u.id}
                        >
                          <option value="STD">{t('roles.STD')}</option>
                          <option value="PAR">{t('roles.PAR')}</option>
                          <option value="TCH">{t('roles.TCH')}</option>
                          <option value="DIR">{t('roles.DIR')}</option>
                        </select>
                      ) : (
                        <span className="role-badge">{t(`roles.${u.role}`, u.role)}</span>
                      )}
                    </td>
                    <td>
                      <span
                        className="status-badge"
                        style={{
                          color: getStatusColor(u.status),
                          borderColor: getStatusColor(u.status),
                        }}
                      >
                        {t(`admin.users.status${u.status.charAt(0).toUpperCase() + u.status.slice(1)}`, u.status)}
                      </span>
                    </td>
                    <td>{formatDate(u.created_at, i18n.language)}</td>
                    <td>
                      {currentUser?.role === 'ADM' && u.id !== currentUser?.id && (
                        <>
                          {u.status === 'active' ? (
                            <button
                              className="btn btn-danger btn-sm"
                              onClick={() => handleSuspend(u.id)}
                              disabled={actionLoading === u.id}
                            >
                              {t('admin.users.suspend')}
                            </button>
                          ) : u.status === 'suspended' ? (
                            <button
                              className="btn btn-primary btn-sm"
                              onClick={() => handleActivate(u.id)}
                              disabled={actionLoading === u.id}
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
