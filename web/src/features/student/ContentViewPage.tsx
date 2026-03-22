/**
 * Student Content View — view assigned content (video/audio/PDF players), progress tracking.
 *
 * Phase 10B — Student views class content with HTML5 players.
 * API: GET /classes/{classId}/content, GET /content-items/{id},
 *      GET /content-items/{id}/assets/{assetId}, POST /content-items/{id}/progress
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError, getAccessToken } from '@/services/api/client';
import { LoadingState } from '@/shared/ui/LoadingState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { EmptyState } from '@/shared/ui/EmptyState';

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */
interface ClassOption {
  class_id: string;
  class_name: string;
}

interface ClassContent {
  id: string;
  content_item_id: string;
  title: string;
  content_type: string;
  level_band: string | null;
  language: string | null;
  subject: string | null;
  description: string | null;
  assigned_at: string | null;
  teacher_notes: string | null;
}

/* ------------------------------------------------------------------ */
/* Main                                                                */
/* ------------------------------------------------------------------ */
export function ContentViewPage() {
  const { t } = useTranslation();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [classes, setClasses] = useState<ClassOption[]>([]);
  const [selectedClassId, setSelectedClassId] = useState('');
  const [contentItems, setContentItems] = useState<ClassContent[]>([]);
  const [viewingItem, setViewingItem] = useState<ClassContent | null>(null);
  const [progressMap, setProgressMap] = useState<Record<string, string>>({});

  // Fetch enrolled classes
  const fetchClasses = useCallback(async () => {
    try {
      // Student gets their enrollments/classes
      const resp = await api.list<ClassOption>('/enrollments');
      setClasses(resp.data);
      if (resp.data.length > 0 && !selectedClassId) {
        setSelectedClassId(resp.data[0].class_id);
      }
    } catch {
      // Fallback — maybe single class
    }
  }, [selectedClassId]);

  const fetchContent = useCallback(async () => {
    if (!selectedClassId) return;
    try {
      const resp = await api.list<ClassContent>(`/classes/${selectedClassId}/content`);
      setContentItems(resp.data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [selectedClassId, t]);

  useEffect(() => {
    setLoading(true);
    fetchClasses().then(() => setLoading(false));
  }, [fetchClasses]);

  useEffect(() => {
    if (selectedClassId) fetchContent();
  }, [selectedClassId, fetchContent]);

  async function handleUpdateProgress(contentItemId: string, status: string) {
    try {
      await api.post(`/content-items/${contentItemId}/progress`, { status });
      setProgressMap((prev) => ({ ...prev, [contentItemId]: status }));
    } catch { /* ignore */ }
  }

  if (loading) return <LoadingState />;

  const typeIcon: Record<string, string> = {
    video: '🎬',
    audio: '🎵',
    pdf: '📄',
    interactive: '🎮',
  };

  return (
    <div className="page">
      <h1 className="page-title">{t('studentContent.title')}</h1>
      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={fetchContent} />

      {/* Class selector */}
      {classes.length > 1 && (
        <div className="filters-bar" style={{ marginBottom: 16 }}>
          <select className="filter-select" value={selectedClassId} onChange={(e) => setSelectedClassId(e.target.value)}>
            {classes.map((c) => (
              <option key={c.class_id} value={c.class_id}>{c.class_name}</option>
            ))}
          </select>
        </div>
      )}

      {/* Content viewer */}
      {viewingItem ? (
        <ContentPlayer
          item={viewingItem}
          onBack={() => setViewingItem(null)}
          onProgressUpdate={(status) => handleUpdateProgress(viewingItem.content_item_id, status)}
          progress={progressMap[viewingItem.content_item_id]}
        />
      ) : (
        <>
          {contentItems.length === 0 ? (
            <EmptyState message={t('studentContent.empty')} />
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 16 }}>
              {contentItems.map((item) => {
                const prog = progressMap[item.content_item_id];
                return (
                  <div
                    key={item.id}
                    className="card"
                    style={{ padding: 16, cursor: 'pointer' }}
                    onClick={() => {
                      setViewingItem(item);
                      if (!prog) handleUpdateProgress(item.content_item_id, 'in_progress');
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                      <span style={{ fontSize: 20 }}>{typeIcon[item.content_type] || '📚'}</span>
                      <span className="badge" style={{ fontSize: 11 }}>{item.content_type}</span>
                    </div>
                    <h4 style={{ margin: '0 0 4px', fontSize: 14 }}>{item.title}</h4>
                    {item.description && (
                      <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', margin: '0 0 8px', lineHeight: 1.4 }}>
                        {item.description.length > 80 ? item.description.slice(0, 80) + '...' : item.description}
                      </p>
                    )}
                    {item.subject && (
                      <div style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>
                        {t(`cms.subjects.${item.subject}`, item.subject)}
                      </div>
                    )}
                    {item.teacher_notes && (
                      <div style={{ fontSize: 11, color: 'var(--color-primary)', marginTop: 4, fontStyle: 'italic' }}>
                        {item.teacher_notes}
                      </div>
                    )}
                    {/* Progress indicator */}
                    {prog && (
                      <div style={{ marginTop: 8 }}>
                        <span
                          style={{
                            fontSize: 11,
                            padding: '2px 6px',
                            borderRadius: 4,
                            background: prog === 'completed' ? 'var(--color-success)' : 'var(--color-warning)',
                            color: '#fff',
                          }}
                        >
                          {t(`content.progress.${prog}`, prog)}
                        </span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}

/* ================================================================== */
/* Content Player                                                      */
/* ================================================================== */
function ContentPlayer({
  item,
  onBack,
  onProgressUpdate,
  progress,
}: {
  item: ClassContent;
  onBack: () => void;
  onProgressUpdate: (status: string) => void;
  progress: string | undefined;
}) {
  const { t } = useTranslation();
  const token = getAccessToken();
  // Build URL for first asset (we use content-items/{id}/assets endpoint)
  // For simplicity, we'll embed via the content-items API
  const baseUrl = `/api/v1/content-items/${item.content_item_id}`;

  return (
    <div>
      <button className="btn btn-secondary" onClick={onBack} style={{ marginBottom: 16 }}>
        {t('app.back')}
      </button>

      <div className="card" style={{ padding: 20 }}>
        <h2 style={{ margin: '0 0 8px', fontSize: 18 }}>{item.title}</h2>
        {item.description && (
          <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 16 }}>{item.description}</p>
        )}

        {/* Player area */}
        <div style={{ marginBottom: 16, background: '#000', borderRadius: 8, overflow: 'hidden', minHeight: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {item.content_type === 'video' && (
            <video
              controls
              style={{ width: '100%', maxHeight: 500 }}
              onEnded={() => onProgressUpdate('completed')}
            >
              <source src={`${baseUrl}/stream?token=${token}`} />
              {t('studentContent.videoUnsupported')}
            </video>
          )}

          {item.content_type === 'audio' && (
            <div style={{ padding: 40, width: '100%' }}>
              <audio
                controls
                style={{ width: '100%' }}
                onEnded={() => onProgressUpdate('completed')}
              >
                <source src={`${baseUrl}/stream?token=${token}`} />
                {t('studentContent.audioUnsupported')}
              </audio>
            </div>
          )}

          {item.content_type === 'pdf' && (
            <iframe
              src={`${baseUrl}/stream?token=${token}`}
              style={{ width: '100%', height: 600, border: 'none' }}
              title={item.title}
            />
          )}

          {item.content_type === 'interactive' && (
            <div style={{ color: '#fff', padding: 40, textAlign: 'center' }}>
              <p>{t('studentContent.interactiveHint')}</p>
              <a
                href={`${baseUrl}/stream?token=${token}`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary"
              >
                {t('studentContent.openInteractive')}
              </a>
            </div>
          )}
        </div>

        {/* Progress controls */}
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
            {t('studentContent.progress')}:
          </span>
          {progress === 'completed' ? (
            <span style={{ fontSize: 13, color: 'var(--color-success)', fontWeight: 600 }}>
              {t('content.progress.completed')}
            </span>
          ) : (
            <button
              className="btn btn-primary"
              style={{ fontSize: 12, padding: '4px 12px' }}
              onClick={() => onProgressUpdate('completed')}
            >
              {t('studentContent.markComplete')}
            </button>
          )}
        </div>

        {item.teacher_notes && (
          <div style={{ marginTop: 16, padding: 12, background: 'var(--color-bg)', borderRadius: 'var(--radius)', fontSize: 13 }}>
            <strong>{t('studentContent.teacherNotes')}:</strong> {item.teacher_notes}
          </div>
        )}
      </div>
    </div>
  );
}
