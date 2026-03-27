/**
 * Announcements page — list + create/publish for ADM/DIR.
 *
 * Reference: Phase 12A — Announcements UI
 * Calls GET /announcements, POST /announcements, PUT /announcements/{id},
 *        POST /announcements/{id}/publish.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';
import { formatDate } from '@/shared/i18n';

interface Announcement {
  id: string;
  school_id: string;
  author_id: string;
  title: string;
  body: string;
  target_roles: string[];
  target_class_ids: string[];
  published_at: string | null;
  status: string;
  created_at: string;
  updated_at: string | null;
}

const ALL_ROLES = ['ADM', 'DIR', 'TCH', 'PAR', 'STD'];

export function AnnouncementsPage() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const role = user?.role || '';
  const canManage = role === 'ADM' || role === 'DIR';

  const [items, setItems] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('');

  // Create/edit form
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formTitle, setFormTitle] = useState('');
  const [formBody, setFormBody] = useState('');
  const [formTargetRoles, setFormTargetRoles] = useState<string[]>([...ALL_ROLES]);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState<string | null>(null);

  const fetchAnnouncements = useCallback(async (cursor?: string) => {
    try {
      const params: Record<string, string | number | undefined> = { limit: 20 };
      if (cursor) params.cursor = cursor;
      if (statusFilter) params.status = statusFilter;

      const resp = await api.list<Announcement>('/announcements', params);
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
    fetchAnnouncements().finally(() => setLoading(false));
  }, [fetchAnnouncements]);

  async function handleSave() {
    setSaving(true);
    try {
      const payload = {
        title: formTitle,
        body: formBody,
        target_roles: formTargetRoles,
      };

      if (editingId) {
        await api.put(`/announcements/${editingId}`, payload);
      } else {
        await api.post('/announcements', payload);
      }
      setShowForm(false);
      resetForm();
      await fetchAnnouncements();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setSaving(false);
    }
  }

  async function handlePublish(id: string) {
    setPublishing(id);
    try {
      await api.post(`/announcements/${id}/publish`);
      await fetchAnnouncements();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setPublishing(null);
    }
  }

  function openEdit(ann: Announcement) {
    setFormTitle(ann.title);
    setFormBody(ann.body);
    setFormTargetRoles(ann.target_roles);
    setEditingId(ann.id);
    setShowForm(true);
  }

  function resetForm() {
    setFormTitle('');
    setFormBody('');
    setFormTargetRoles([...ALL_ROLES]);
    setEditingId(null);
  }

  function toggleRole(roleCode: string) {
    setFormTargetRoles((prev) =>
      prev.includes(roleCode)
        ? prev.filter((r) => r !== roleCode)
        : [...prev, roleCode]
    );
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'PUBLISHED': return '#10b981';
      case 'DRAFT': return '#f59e0b';
      case 'ARCHIVED': return '#6b7280';
      default: return '#6b7280';
    }
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>{t('announcements.title')}</h1>
        {canManage && (
          <button className="btn btn-primary" onClick={() => { resetForm(); setShowForm(true); }}>
            + {t('announcements.create')}
          </button>
        )}
      </div>

      {canManage && (
        <div className="filters-bar">
          <select
            className="filter-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">{t('announcements.allStatuses')}</option>
            <option value="DRAFT">{t('announcements.statusDraft')}</option>
            <option value="PUBLISHED">{t('announcements.statusPublished')}</option>
            <option value="ARCHIVED">{t('announcements.statusArchived')}</option>
          </select>
        </div>
      )}

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={() => fetchAnnouncements()} />

      {items.length === 0 ? (
        <EmptyState message={t('announcements.empty')} icon="📢" />
      ) : (
        <div className="card-list">
          {items.map((ann) => (
            <div key={ann.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span
                      className="status-badge"
                      style={{ color: getStatusColor(ann.status), borderColor: getStatusColor(ann.status) }}
                    >
                      {t(`announcements.status${ann.status.charAt(0) + ann.status.slice(1).toLowerCase()}`, ann.status)}
                    </span>
                    <div style={{ display: 'flex', gap: 4 }}>
                      {ann.target_roles.map((r) => (
                        <span key={r} className="permission-badge">{t(`roles.${r}`, r)}</span>
                      ))}
                    </div>
                  </div>
                  <h3 style={{ fontSize: 16, fontWeight: 600 }}>{ann.title}</h3>
                </div>
                <span style={{ fontSize: 12, color: 'var(--color-text-secondary)', whiteSpace: 'nowrap' }}>
                  {formatDate(ann.published_at || ann.created_at, i18n.language)}
                </span>
              </div>
              <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                {ann.body}
              </p>
              {canManage && ann.status === 'DRAFT' && (
                <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                  <button className="btn btn-sm btn-secondary" onClick={() => openEdit(ann)}>
                    ✏️ {t('announcements.edit')}
                  </button>
                  <button
                    className="btn btn-sm btn-primary"
                    onClick={() => handlePublish(ann.id)}
                    disabled={publishing === ann.id}
                  >
                    {publishing === ann.id ? t('app.loading') : `📣 ${t('announcements.publish')}`}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {hasMore && (
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <button className="btn btn-secondary" onClick={() => fetchAnnouncements(nextCursor || undefined)}>
            {t('feed.loadMore')}
          </button>
        </div>
      )}

      {/* Create/Edit Modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ marginBottom: 16 }}>
              {editingId ? t('announcements.edit') : t('announcements.create')}
            </h2>
            <div className="form-field">
              <label>{t('announcements.formTitle')}</label>
              <input
                type="text"
                value={formTitle}
                onChange={(e) => setFormTitle(e.target.value)}
                placeholder={t('announcements.titlePlaceholder')}
              />
            </div>
            <div className="form-field">
              <label>{t('announcements.formBody')}</label>
              <textarea
                className="filter-input"
                rows={5}
                value={formBody}
                onChange={(e) => setFormBody(e.target.value)}
                placeholder={t('announcements.bodyPlaceholder')}
                style={{ width: '100%' }}
              />
            </div>
            <div className="form-field">
              <label>{t('announcements.targetRoles')}</label>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {ALL_ROLES.map((r) => (
                  <label key={r} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={formTargetRoles.includes(r)}
                      onChange={() => toggleRole(r)}
                    />
                    {t(`roles.${r}`, r)}
                  </label>
                ))}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <button
                className="btn btn-primary"
                onClick={handleSave}
                disabled={saving || !formTitle || !formBody}
              >
                {saving ? t('app.loading') : t('app.save')}
              </button>
              <button className="btn btn-secondary" onClick={() => setShowForm(false)}>
                {t('app.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
