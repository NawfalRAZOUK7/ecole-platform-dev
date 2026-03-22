/**
 * Admin Parent-Child Links page — list, create, and revoke parent-child links.
 *
 * Reference: Phase 4D-patch — Parent-Child Link UI
 * Calls GET /admin/parent-child-links, POST /admin/parent-child-links, DELETE /admin/parent-child-links/{id}.
 * Calls GET /admin/users for parent/student search dropdowns.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError, getAccessToken } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';
import { formatDate } from '@/shared/i18n';

interface ParentChildLink {
  id: string;
  parent_user_id: string;
  child_user_id: string;
  school_id: string;
  status: string;
  linked_at: string | null;
  linked_by: string | null;
}

interface UserEntry {
  id: string;
  full_name: string;
  email: string;
  role: string;
}

export function ParentChildLinksPage() {
  const { t, i18n } = useTranslation();
  const [links, setLinks] = useState<ParentChildLink[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  const [revoking, setRevoking] = useState<string | null>(null);

  // Create link state
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);

  // Parent search
  const [parentSearch, setParentSearch] = useState('');
  const [parentResults, setParentResults] = useState<UserEntry[]>([]);
  const [selectedParent, setSelectedParent] = useState<UserEntry | null>(null);
  const [parentSearching, setParentSearching] = useState(false);

  // Student search
  const [studentSearch, setStudentSearch] = useState('');
  const [studentResults, setStudentResults] = useState<UserEntry[]>([]);
  const [selectedStudent, setSelectedStudent] = useState<UserEntry | null>(null);
  const [studentSearching, setStudentSearching] = useState(false);

  // User name cache for display
  const [userNames, setUserNames] = useState<Record<string, string>>({});

  const fetchLinks = useCallback(async (cursor?: string) => {
    try {
      const params: Record<string, string | number | undefined> = {};
      if (cursor) params.cursor = cursor;
      if (statusFilter) params.status = statusFilter;

      const resp = await api.list<ParentChildLink>('/admin/parent-child-links', params);
      const newLinks = cursor ? [...links, ...resp.data] : resp.data;
      setLinks(cursor ? (prev) => [...prev, ...resp.data] : resp.data);
      setNextCursor(resp.meta.next_cursor);
      setHasMore(resp.meta.has_more);
      setError(null);

      // Fetch user names for display
      const allLinks = cursor ? newLinks : resp.data;
      const userIds = new Set<string>();
      for (const link of allLinks) {
        if (!userNames[link.parent_user_id]) userIds.add(link.parent_user_id);
        if (!userNames[link.child_user_id]) userIds.add(link.child_user_id);
      }
      if (userIds.size > 0) {
        await fetchUserNames(Array.from(userIds));
      }
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [t, statusFilter]);

  async function fetchUserNames(ids: string[]) {
    // Fetch user info for each ID not already cached
    const newNames: Record<string, string> = {};
    for (const id of ids) {
      try {
        const resp = await api.get<{ email: string; full_name: string; role: string }>(`/admin/users/${id}/profile`);
        newNames[id] = resp.data.full_name || resp.data.email;
      } catch {
        newNames[id] = id.slice(0, 8) + '...';
      }
    }
    setUserNames((prev) => ({ ...prev, ...newNames }));
  }

  useEffect(() => {
    setLoading(true);
    fetchLinks().finally(() => setLoading(false));
  }, [fetchLinks]);

  // Search parents
  useEffect(() => {
    if (parentSearch.length < 2) {
      setParentResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setParentSearching(true);
      try {
        const resp = await api.list<UserEntry>('/admin/users', {
          search: parentSearch,
          role: 'PAR',
        });
        setParentResults(resp.data);
      } catch { /* ignore */ }
      setParentSearching(false);
    }, 300);
    return () => clearTimeout(timer);
  }, [parentSearch]);

  // Search students
  useEffect(() => {
    if (studentSearch.length < 2) {
      setStudentResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setStudentSearching(true);
      try {
        const resp = await api.list<UserEntry>('/admin/users', {
          search: studentSearch,
          role: 'STD',
        });
        setStudentResults(resp.data);
      } catch { /* ignore */ }
      setStudentSearching(false);
    }, 300);
    return () => clearTimeout(timer);
  }, [studentSearch]);

  async function handleRevoke(linkId: string) {
    if (!window.confirm(t('admin.parentChildLinks.confirmRevoke'))) return;
    setRevoking(linkId);
    try {
      await api.delete(`/admin/parent-child-links/${linkId}`);
      setLinks((prev) => prev.map((l) =>
        l.id === linkId ? { ...l, status: 'revoked' } : l
      ));
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
    setRevoking(null);
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'active': return '#10b981';
      case 'revoked': return '#ef4444';
      default: return '#6b7280';
    }
  }

  async function handleCreateLink() {
    if (!selectedParent || !selectedStudent) return;
    setCreating(true);
    try {
      const token = getAccessToken();
      const resp = await fetch(
        `/api/v1/admin/parent-child-links?parent_user_id=${encodeURIComponent(selectedParent.id)}&child_user_id=${encodeURIComponent(selectedStudent.id)}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'application/json',
          },
          credentials: 'include',
        }
      );
      if (!resp.ok) {
        const body = await resp.json().catch(() => null);
        throw new Error(body?.error?.message || t('app.error'));
      }
      setSelectedParent(null);
      setSelectedStudent(null);
      setParentSearch('');
      setStudentSearch('');
      setShowCreate(false);
      fetchLinks();
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    }
    setCreating(false);
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>{t('admin.parentChildLinks.title')}</h1>
        <button className="btn btn-primary" onClick={() => setShowCreate(!showCreate)}>
          {t('admin.parentChildLinks.create')}
        </button>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={() => fetchLinks()} />

      {/* Create link form */}
      {showCreate && (
        <div className="card" style={{ marginBottom: 20 }}>
          <h3 style={{ marginBottom: 12, fontSize: 15, fontWeight: 600 }}>{t('admin.parentChildLinks.createNew')}</h3>

          {/* Parent search */}
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, marginBottom: 4 }}>
              {t('admin.parentChildLinks.selectParent')}
            </label>
            {selectedParent ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)' }}>
                <span>{selectedParent.full_name} ({selectedParent.email})</span>
                <button className="btn btn-sm" onClick={() => { setSelectedParent(null); setParentSearch(''); }} style={{ marginLeft: 'auto', fontSize: 12 }}>&times;</button>
              </div>
            ) : (
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  className="filter-input"
                  placeholder={t('admin.parentChildLinks.searchParent')}
                  value={parentSearch}
                  onChange={(e) => setParentSearch(e.target.value)}
                  style={{ width: '100%' }}
                />
                {parentSearching && <span style={{ position: 'absolute', right: 8, top: 8, fontSize: 12 }}>{t('app.loading')}</span>}
                {parentResults.length > 0 && (
                  <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', maxHeight: 200, overflowY: 'auto', zIndex: 10 }}>
                    {parentResults.map((u) => (
                      <div
                        key={u.id}
                        onClick={() => { setSelectedParent(u); setParentResults([]); setParentSearch(''); }}
                        style={{ padding: '8px 12px', cursor: 'pointer', fontSize: 13, borderBottom: '1px solid var(--color-border)' }}
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

          {/* Student search */}
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 500, marginBottom: 4 }}>
              {t('admin.parentChildLinks.selectStudent')}
            </label>
            {selectedStudent ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)' }}>
                <span>{selectedStudent.full_name} ({selectedStudent.email})</span>
                <button className="btn btn-sm" onClick={() => { setSelectedStudent(null); setStudentSearch(''); }} style={{ marginLeft: 'auto', fontSize: 12 }}>&times;</button>
              </div>
            ) : (
              <div style={{ position: 'relative' }}>
                <input
                  type="text"
                  className="filter-input"
                  placeholder={t('admin.parentChildLinks.searchStudent')}
                  value={studentSearch}
                  onChange={(e) => setStudentSearch(e.target.value)}
                  style={{ width: '100%' }}
                />
                {studentSearching && <span style={{ position: 'absolute', right: 8, top: 8, fontSize: 12 }}>{t('app.loading')}</span>}
                {studentResults.length > 0 && (
                  <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', maxHeight: 200, overflowY: 'auto', zIndex: 10 }}>
                    {studentResults.map((u) => (
                      <div
                        key={u.id}
                        onClick={() => { setSelectedStudent(u); setStudentResults([]); setStudentSearch(''); }}
                        style={{ padding: '8px 12px', cursor: 'pointer', fontSize: 13, borderBottom: '1px solid var(--color-border)' }}
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

          <button
            className="btn btn-primary"
            onClick={handleCreateLink}
            disabled={creating || !selectedParent || !selectedStudent}
          >
            {creating ? t('app.loading') : t('admin.parentChildLinks.linkBtn')}
          </button>
        </div>
      )}

      {/* Filters */}
      <div className="filters-bar">
        <select className="filter-select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">{t('admin.parentChildLinks.allStatuses')}</option>
          <option value="active">{t('admin.parentChildLinks.statusActive')}</option>
          <option value="revoked">{t('admin.parentChildLinks.statusRevoked')}</option>
        </select>
      </div>

      {/* Links table */}
      {links.length === 0 ? (
        <EmptyState message={t('admin.parentChildLinks.empty')} icon="🔗" />
      ) : (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('admin.parentChildLinks.parent')}</th>
                  <th>{t('admin.parentChildLinks.student')}</th>
                  <th>{t('admin.parentChildLinks.status')}</th>
                  <th>{t('admin.parentChildLinks.linkedAt')}</th>
                  <th>{t('admin.users.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {links.map((link) => (
                  <tr key={link.id}>
                    <td>{userNames[link.parent_user_id] || link.parent_user_id.slice(0, 8) + '...'}</td>
                    <td>{userNames[link.child_user_id] || link.child_user_id.slice(0, 8) + '...'}</td>
                    <td>
                      <span
                        className="status-badge"
                        style={{ color: getStatusColor(link.status), borderColor: getStatusColor(link.status) }}
                      >
                        {t(`admin.parentChildLinks.status${link.status.charAt(0).toUpperCase() + link.status.slice(1)}`, link.status)}
                      </span>
                    </td>
                    <td>{formatDate(link.linked_at, i18n.language)}</td>
                    <td>
                      {link.status === 'active' && (
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => handleRevoke(link.id)}
                          disabled={revoking === link.id}
                        >
                          {t('admin.parentChildLinks.revoke')}
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
              <button className="btn btn-secondary" onClick={() => fetchLinks(nextCursor!)}>
                {t('feed.loadMore')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
