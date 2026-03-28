import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { formatDate } from '@/shared/i18n';
import {
  useAnnouncements,
  useCreateAnnouncement,
  usePublishAnnouncement,
  useUpdateAnnouncement,
} from './useAnnouncements';
import type { Announcement } from './announcements.service';

const ALL_ROLES = ['ADM', 'DIR', 'TCH', 'PAR', 'STD'];

export function AnnouncementsPage() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const role = user?.role || '';
  const canManage = role === 'ADM' || role === 'DIR';
  const [statusFilter, setStatusFilter] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formTitle, setFormTitle] = useState('');
  const [formBody, setFormBody] = useState('');
  const [formTargetRoles, setFormTargetRoles] = useState<string[]>([...ALL_ROLES]);
  const [publishingId, setPublishingId] = useState<string | null>(null);
  const announcementsQuery = useAnnouncements({ status: statusFilter || undefined });
  const createAnnouncementMutation = useCreateAnnouncement();
  const updateAnnouncementMutation = useUpdateAnnouncement();
  const publishAnnouncementMutation = usePublishAnnouncement();

  const items = useMemo(
    () => announcementsQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [announcementsQuery.data]
  );
  const saving = createAnnouncementMutation.isPending || updateAnnouncementMutation.isPending;

  if (announcementsQuery.isLoading) {
    return <LoadingState />;
  }

  function resetForm() {
    setFormTitle('');
    setFormBody('');
    setFormTargetRoles([...ALL_ROLES]);
    setEditingId(null);
  }

  function openEdit(announcement: Announcement) {
    setFormTitle(announcement.title);
    setFormBody(announcement.body);
    setFormTargetRoles(announcement.target_roles);
    setEditingId(announcement.id);
    setShowForm(true);
  }

  function toggleRole(roleCode: string) {
    setFormTargetRoles((previous) =>
      previous.includes(roleCode)
        ? previous.filter((item) => item !== roleCode)
        : [...previous, roleCode]
    );
  }

  async function handleSave() {
    setError(null);

    try {
      if (editingId) {
        await updateAnnouncementMutation.mutateAsync({
          announcementId: editingId,
          payload: {
            title: formTitle,
            body: formBody,
            target_roles: formTargetRoles,
          },
        });
      } else {
        await createAnnouncementMutation.mutateAsync({
          title: formTitle,
          body: formBody,
          target_roles: formTargetRoles,
        });
      }
      resetForm();
      setShowForm(false);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : t('app.error'));
    }
  }

  async function handlePublish(announcementId: string) {
    setPublishingId(announcementId);
    setError(null);

    try {
      await publishAnnouncementMutation.mutateAsync(announcementId);
    } catch (publishError) {
      setError(publishError instanceof Error ? publishError.message : t('app.error'));
    } finally {
      setPublishingId(null);
    }
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'PUBLISHED':
        return '#10b981';
      case 'DRAFT':
        return '#f59e0b';
      case 'ARCHIVED':
        return '#6b7280';
      default:
        return '#6b7280';
    }
  }

  return (
    <div className="page">
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 24,
        }}
      >
        <h1 className="page-title" style={{ marginBottom: 0 }}>
          {t('announcements.title')}
        </h1>
        {canManage ? (
          <button
            className="btn btn-primary"
            onClick={() => {
              resetForm();
              setShowForm(true);
            }}
          >
            + {t('announcements.create')}
          </button>
        ) : null}
      </div>

      {canManage ? (
        <div className="filters-bar">
          <select
            className="filter-select"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
          >
            <option value="">{t('announcements.allStatuses')}</option>
            <option value="DRAFT">{t('announcements.statusDraft')}</option>
            <option value="PUBLISHED">{t('announcements.statusPublished')}</option>
            <option value="ARCHIVED">{t('announcements.statusArchived')}</option>
          </select>
        </div>
      ) : null}

      <ErrorBanner
        error={error || (announcementsQuery.error instanceof Error ? announcementsQuery.error.message : null)}
        onDismiss={() => setError(null)}
        onRetry={() => void announcementsQuery.refetch()}
      />

      {items.length === 0 ? (
        <EmptyState message={t('announcements.empty')} icon="📢" />
      ) : (
        <div className="card-list">
          {items.map((announcement) => (
            <div key={announcement.id} className="card">
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  marginBottom: 8,
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span
                      className="status-badge"
                      style={{
                        color: getStatusColor(announcement.status),
                        borderColor: getStatusColor(announcement.status),
                      }}
                    >
                      {t(
                        `announcements.status${announcement.status.charAt(0) + announcement.status.slice(1).toLowerCase()}`,
                        announcement.status
                      )}
                    </span>
                    <div style={{ display: 'flex', gap: 4 }}>
                      {announcement.target_roles.map((targetRole) => (
                        <span key={targetRole} className="permission-badge">
                          {t(`roles.${targetRole}`, targetRole)}
                        </span>
                      ))}
                    </div>
                  </div>
                  <h3 style={{ fontSize: 16, fontWeight: 600 }}>{announcement.title}</h3>
                </div>
                <span
                  style={{
                    fontSize: 12,
                    color: 'var(--color-text-secondary)',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {formatDate(announcement.published_at || announcement.created_at, i18n.language)}
                </span>
              </div>
              <p
                style={{
                  fontSize: 14,
                  color: 'var(--color-text-secondary)',
                  lineHeight: 1.6,
                  whiteSpace: 'pre-wrap',
                }}
              >
                {announcement.body}
              </p>
              {canManage && announcement.status === 'DRAFT' ? (
                <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                  <button className="btn btn-sm btn-secondary" onClick={() => openEdit(announcement)}>
                    ✏️ {t('announcements.edit')}
                  </button>
                  <button
                    className="btn btn-sm btn-primary"
                    onClick={() => void handlePublish(announcement.id)}
                    disabled={publishingId === announcement.id}
                  >
                    {publishingId === announcement.id ? t('app.loading') : `📣 ${t('announcements.publish')}`}
                  </button>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      )}

      {announcementsQuery.hasNextPage ? (
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <button
            className="btn btn-secondary"
            onClick={() => void announcementsQuery.fetchNextPage()}
            disabled={announcementsQuery.isFetchingNextPage}
          >
            {announcementsQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
          </button>
        </div>
      ) : null}

      {showForm ? (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <h2 style={{ marginBottom: 16 }}>
              {editingId ? t('announcements.edit') : t('announcements.create')}
            </h2>
            <div className="form-field">
              <label>{t('announcements.formTitle')}</label>
              <input
                type="text"
                value={formTitle}
                onChange={(event) => setFormTitle(event.target.value)}
                placeholder={t('announcements.titlePlaceholder')}
              />
            </div>
            <div className="form-field">
              <label>{t('announcements.formBody')}</label>
              <textarea
                className="filter-input"
                rows={5}
                value={formBody}
                onChange={(event) => setFormBody(event.target.value)}
                placeholder={t('announcements.bodyPlaceholder')}
                style={{ width: '100%' }}
              />
            </div>
            <div className="form-field">
              <label>{t('announcements.targetRoles')}</label>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {ALL_ROLES.map((targetRole) => (
                  <label key={targetRole} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={formTargetRoles.includes(targetRole)}
                      onChange={() => toggleRole(targetRole)}
                    />
                    {t(`roles.${targetRole}`, targetRole)}
                  </label>
                ))}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <button
                className="btn btn-primary"
                onClick={() => void handleSave()}
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
      ) : null}
    </div>
  );
}
