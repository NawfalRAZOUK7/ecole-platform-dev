/**
 * Admin Parent-Child Links page — list, create, and revoke parent-child links.
 *
 * Reference: Phase 4D-patch — Parent-Child Link UI
 * Calls GET /admin/parent-child-links, POST /admin/parent-child-links, DELETE /admin/parent-child-links/{id}.
 * Calls GET /admin/users for parent/student search dropdowns.
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
  useAdminParentChildLinks,
  useAdminUserSearch,
  useCreateParentChildLink,
  useRevokeParentChildLink,
} from './useAdmin';
import type { ParentChildLinkRow, UserItem } from './admin.service';

export function ParentChildLinksPage() {
  const { t, i18n } = useTranslation();
  const [statusFilter, setStatusFilter] = useState('');
  const [revoking, setRevoking] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [parentSearch, setParentSearch] = useState('');
  const [parentSearchQuery, setParentSearchQuery] = useState('');
  const [selectedParent, setSelectedParent] = useState<UserItem | null>(null);
  const [studentSearch, setStudentSearch] = useState('');
  const [studentSearchQuery, setStudentSearchQuery] = useState('');
  const [selectedStudent, setSelectedStudent] = useState<UserItem | null>(null);

  const linksQuery = useAdminParentChildLinks({
    status: statusFilter || undefined,
  });
  const parentSearchResults = useAdminUserSearch(parentSearchQuery, 'PAR');
  const studentSearchResults = useAdminUserSearch(studentSearchQuery, 'STD');
  const createLinkMutation = useCreateParentChildLink();
  const revokeLinkMutation = useRevokeParentChildLink();

  const links: ParentChildLinkRow[] = useMemo(
    () => linksQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [linksQuery.data]
  );
  const dismissibleError = useDismissibleError(
    useMemo(
      () => toBannerError(linksQuery.error ?? createLinkMutation.error ?? revokeLinkMutation.error, t('app.error')),
      [createLinkMutation.error, linksQuery.error, revokeLinkMutation.error, t]
    )
  );

  useEffect(() => {
    if (parentSearch.length < 2) {
      setParentSearchQuery('');
      return;
    }
    const timer = window.setTimeout(() => setParentSearchQuery(parentSearch), 300);
    return () => window.clearTimeout(timer);
  }, [parentSearch]);

  useEffect(() => {
    if (studentSearch.length < 2) {
      setStudentSearchQuery('');
      return;
    }
    const timer = window.setTimeout(() => setStudentSearchQuery(studentSearch), 300);
    return () => window.clearTimeout(timer);
  }, [studentSearch]);

  async function handleRevoke(linkId: string) {
    if (!window.confirm(t('admin.parentChildLinks.confirmRevoke'))) return;
    setRevoking(linkId);
    await revokeLinkMutation.mutateAsync(linkId);
    await linksQuery.refetch();
    setRevoking(null);
  }

  async function handleCreateLink() {
    if (!selectedParent || !selectedStudent) return;
    setCreating(true);
    await createLinkMutation.mutateAsync({
      parentUserId: selectedParent.id,
      childUserId: selectedStudent.id,
    });
    await linksQuery.refetch();
    setSelectedParent(null);
    setSelectedStudent(null);
    setParentSearch('');
    setStudentSearch('');
    setParentSearchQuery('');
    setStudentSearchQuery('');
    setShowCreate(false);
    setCreating(false);
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'active':
        return '#10b981';
      case 'revoked':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  }

  if (linksQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>{t('admin.parentChildLinks.title')}</h1>
        <button className="btn btn-primary" onClick={() => setShowCreate(!showCreate)}>
          {t('admin.parentChildLinks.create')}
        </button>
      </div>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void linksQuery.refetch()}
      />

      {showCreate && (
        <div className="card" style={{ marginBottom: 20 }}>
          <h3 style={{ marginBottom: 12, fontSize: 15, fontWeight: 600 }}>{t('admin.parentChildLinks.createNew')}</h3>

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
                {parentSearchResults.isFetching && <span style={{ position: 'absolute', right: 8, top: 8, fontSize: 12 }}>{t('app.loading')}</span>}
                {(parentSearchResults.data ?? []).length > 0 && (
                  <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', maxHeight: 200, overflowY: 'auto', zIndex: 10 }}>
                    {(parentSearchResults.data ?? []).map((user) => (
                      <div
                        key={user.id}
                        onClick={() => { setSelectedParent(user); setParentSearch(''); setParentSearchQuery(''); }}
                        style={{ padding: '8px 12px', cursor: 'pointer', fontSize: 13, borderBottom: '1px solid var(--color-border)' }}
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
                {studentSearchResults.isFetching && <span style={{ position: 'absolute', right: 8, top: 8, fontSize: 12 }}>{t('app.loading')}</span>}
                {(studentSearchResults.data ?? []).length > 0 && (
                  <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', maxHeight: 200, overflowY: 'auto', zIndex: 10 }}>
                    {(studentSearchResults.data ?? []).map((user) => (
                      <div
                        key={user.id}
                        onClick={() => { setSelectedStudent(user); setStudentSearch(''); setStudentSearchQuery(''); }}
                        style={{ padding: '8px 12px', cursor: 'pointer', fontSize: 13, borderBottom: '1px solid var(--color-border)' }}
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

          <button
            className="btn btn-primary"
            onClick={() => void handleCreateLink()}
            disabled={creating || !selectedParent || !selectedStudent}
          >
            {creating ? t('app.loading') : t('admin.parentChildLinks.linkBtn')}
          </button>
        </div>
      )}

      <div className="filters-bar">
        <select className="filter-select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">{t('admin.parentChildLinks.allStatuses')}</option>
          <option value="active">{t('admin.parentChildLinks.statusActive')}</option>
          <option value="revoked">{t('admin.parentChildLinks.statusRevoked')}</option>
        </select>
      </div>

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
                    <td>{link.parent_name}</td>
                    <td>{link.child_name}</td>
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
                          onClick={() => void handleRevoke(link.id)}
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

          {linksQuery.hasNextPage && (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <button
                className="btn btn-secondary"
                onClick={() => void linksQuery.fetchNextPage()}
                disabled={linksQuery.isFetchingNextPage}
              >
                {linksQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
