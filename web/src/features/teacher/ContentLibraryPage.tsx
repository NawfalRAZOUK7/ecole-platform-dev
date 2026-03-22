/**
 * Teacher Content Library — browse platform + school content, assign to class,
 * upload school-scoped content, submit for platform review, view my submissions.
 *
 * Phase 10B — Teacher Content Library (Web)
 * API: GET /content/library, POST /content/assign, DELETE /content/assign/{id},
 *      POST /content/submit-for-review, GET /content/my-submissions
 */

import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError, getAccessToken } from '@/services/api/client';
import { LoadingState } from '@/shared/ui/LoadingState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { EmptyState } from '@/shared/ui/EmptyState';

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */
interface ContentItem {
  id: string;
  school_id: string | null;
  title: string;
  content_type: string;
  level_band: string | null;
  language: string | null;
  subject: string | null;
  description: string | null;
  origin: string;
  status: string;
}

interface ClassOption {
  id: string;
  name: string;
}

interface MySubmission {
  id: string;
  content_item_id: string;
  content_title: string;
  status: string;
  submitted_at: string | null;
  review_notes: string | null;
  promoted_content_id: string | null;
}

type Tab = 'browse' | 'upload' | 'submissions';

/* ------------------------------------------------------------------ */
/* Main Component                                                      */
/* ------------------------------------------------------------------ */
export function ContentLibraryPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<Tab>('browse');
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="page">
      <h1 className="page-title">{t('teacherContent.title')}</h1>
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      {/* Tab bar */}
      <div className="filters-bar" style={{ marginBottom: 16 }}>
        {(['browse', 'upload', 'submissions'] as Tab[]).map((tb) => (
          <button
            key={tb}
            className={`btn ${tab === tb ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setTab(tb)}
            style={{ marginRight: 8 }}
          >
            {t(`teacherContent.tab_${tb}`)}
          </button>
        ))}
      </div>

      {tab === 'browse' && <BrowseTab onError={setError} />}
      {tab === 'upload' && <UploadTab onError={setError} />}
      {tab === 'submissions' && <SubmissionsTab onError={setError} />}
    </div>
  );
}

/* ================================================================== */
/* Browse Tab                                                          */
/* ================================================================== */
function BrowseTab({ onError }: { onError: (e: string | null) => void }) {
  const { t } = useTranslation();
  const [items, setItems] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [classes, setClasses] = useState<ClassOption[]>([]);

  // Filters
  const [filterType, setFilterType] = useState('');
  const [filterSubject, setFilterSubject] = useState('');
  const [filterLevel, setFilterLevel] = useState('');
  const [filterOrigin, setFilterOrigin] = useState('');
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);

  // Assign modal
  const [assignItem, setAssignItem] = useState<ContentItem | null>(null);
  const [assignClassId, setAssignClassId] = useState('');
  const [assignNotes, setAssignNotes] = useState('');
  const [assigning, setAssigning] = useState(false);

  const fetchItems = useCallback(async (cursor?: string) => {
    try {
      const params: Record<string, string | number | undefined> = {};
      if (filterType) params.content_type = filterType;
      if (filterSubject) params.subject = filterSubject;
      if (filterLevel) params.level_band = filterLevel;
      if (filterOrigin) params.origin = filterOrigin;
      if (cursor) params.cursor = cursor;

      const resp = await api.list<ContentItem>('/content/library', params);
      if (cursor) {
        setItems((prev) => [...prev, ...resp.data]);
      } else {
        setItems(resp.data);
      }
      setNextCursor(resp.meta.next_cursor);
      setHasMore(resp.meta.has_more);
      onError(null);
    } catch (err) {
      onError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [filterType, filterSubject, filterLevel, filterOrigin, onError, t]);

  const fetchClasses = useCallback(async () => {
    try {
      const resp = await api.list<ClassOption>('/classes');
      setClasses(resp.data);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchItems(), fetchClasses()]).finally(() => setLoading(false));
  }, [fetchItems, fetchClasses]);

  async function handleAssign(e: FormEvent) {
    e.preventDefault();
    if (!assignItem || !assignClassId) return;
    setAssigning(true);
    try {
      await api.post('/content/assign', {
        content_item_id: assignItem.id,
        class_id: assignClassId,
        notes: assignNotes.trim() || null,
      });
      setAssignItem(null);
      setAssignClassId('');
      setAssignNotes('');
      onError(null);
    } catch (err) {
      onError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setAssigning(false);
    }
  }

  async function handleSubmitForReview(contentId: string) {
    try {
      await api.post('/content/submit-for-review', { content_item_id: contentId });
      onError(null);
      alert(t('teacherContent.submittedForReview'));
    } catch (err) {
      onError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }

  if (loading) return <LoadingState />;

  return (
    <>
      {/* Filters */}
      <div className="filters-bar" style={{ marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
        <select className="filter-select" value={filterType} onChange={(e) => setFilterType(e.target.value)}>
          <option value="">{t('teacherContent.allTypes')}</option>
          <option value="video">{t('cms.contentTypes.video')}</option>
          <option value="pdf">{t('cms.contentTypes.pdf')}</option>
          <option value="audio">{t('cms.contentTypes.audio')}</option>
          <option value="interactive">{t('cms.contentTypes.interactive')}</option>
        </select>
        <select className="filter-select" value={filterSubject} onChange={(e) => setFilterSubject(e.target.value)}>
          <option value="">{t('teacherContent.allSubjects')}</option>
          {['math', 'french', 'arabic', 'science', 'history', 'geography', 'english'].map((s) => (
            <option key={s} value={s}>{t(`cms.subjects.${s}`, s)}</option>
          ))}
        </select>
        <select className="filter-select" value={filterLevel} onChange={(e) => setFilterLevel(e.target.value)}>
          <option value="">{t('teacherContent.allLevels')}</option>
          {['primaire', 'college', 'lycee'].map((l) => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
        <select className="filter-select" value={filterOrigin} onChange={(e) => setFilterOrigin(e.target.value)}>
          <option value="">{t('teacherContent.allOrigins')}</option>
          <option value="PLATFORM">{t('cms.origins.PLATFORM')}</option>
          <option value="PROMOTED">{t('cms.origins.PROMOTED')}</option>
        </select>
      </div>

      {/* Content grid */}
      {items.length === 0 ? (
        <EmptyState message={t('teacherContent.empty')} />
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
          {items.map((item) => (
            <div key={item.id} className="card" style={{ padding: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                <h4 style={{ margin: 0, fontSize: 14 }}>{item.title}</h4>
                <span className="badge" style={{ fontSize: 11 }}>{item.content_type}</span>
              </div>
              {item.description && (
                <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', margin: '0 0 8px', lineHeight: 1.4 }}>
                  {item.description.length > 100 ? item.description.slice(0, 100) + '...' : item.description}
                </p>
              )}
              <div style={{ fontSize: 11, color: 'var(--color-text-secondary)', marginBottom: 8 }}>
                {item.subject && <span style={{ marginRight: 8 }}>{t(`cms.subjects.${item.subject}`, item.subject)}</span>}
                {item.level_band && <span style={{ marginRight: 8 }}>{item.level_band}</span>}
                <span>{t(`cms.origins.${item.origin}`, item.origin)}</span>
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                <button
                  className="btn btn-primary"
                  style={{ fontSize: 12, padding: '4px 10px' }}
                  onClick={() => { setAssignItem(item); setAssignClassId(''); setAssignNotes(''); }}
                >
                  {t('teacherContent.assignToClass')}
                </button>
                {item.school_id && (
                  <button
                    className="btn btn-secondary"
                    style={{ fontSize: 12, padding: '4px 10px' }}
                    onClick={() => handleSubmitForReview(item.id)}
                  >
                    {t('teacherContent.submitForReview')}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Load more */}
      {hasMore && (
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <button className="btn btn-secondary" onClick={() => fetchItems(nextCursor!)}>
            {t('teacherContent.loadMore')}
          </button>
        </div>
      )}

      {/* Assign modal */}
      {assignItem && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <form className="card" style={{ padding: 24, maxWidth: 400, width: '100%' }} onSubmit={handleAssign}>
            <h3 style={{ margin: '0 0 16px' }}>{t('teacherContent.assignTitle')}</h3>
            <p style={{ fontSize: 13, marginBottom: 12 }}>
              <strong>{assignItem.title}</strong>
            </p>
            <div className="form-field" style={{ marginBottom: 12 }}>
              <label>{t('teacherContent.selectClass')}</label>
              <select className="filter-select" value={assignClassId} onChange={(e) => setAssignClassId(e.target.value)} required style={{ width: '100%' }}>
                <option value="">{t('teacherContent.choosePlaceholder')}</option>
                {classes.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div className="form-field" style={{ marginBottom: 16 }}>
              <label>{t('teacherContent.notes')}</label>
              <input className="filter-input" value={assignNotes} onChange={(e) => setAssignNotes(e.target.value)} placeholder={t('teacherContent.notesPlaceholder')} style={{ width: '100%' }} />
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button type="submit" className="btn btn-primary" disabled={assigning}>
                {assigning ? t('app.loading') : t('teacherContent.assign')}
              </button>
              <button type="button" className="btn btn-secondary" onClick={() => setAssignItem(null)}>
                {t('app.cancel')}
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}

/* ================================================================== */
/* Upload Tab — upload school-scoped content                          */
/* ================================================================== */
function UploadTab({ onError }: { onError: (e: string | null) => void }) {
  const { t } = useTranslation();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [contentType, setContentType] = useState('pdf');
  const [levelBand, setLevelBand] = useState('');
  const [subject, setSubject] = useState('');
  const [language, setLanguage] = useState('fr');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [success, setSuccess] = useState(false);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!title.trim() || !file) return;
    setUploading(true);
    setProgress(0);
    onError(null);

    const formData = new FormData();
    formData.append('title', title.trim());
    if (description.trim()) formData.append('description', description.trim());
    formData.append('content_type', contentType);
    if (levelBand) formData.append('level_band', levelBand);
    if (subject) formData.append('subject', subject);
    formData.append('language', language);
    formData.append('file', file);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/v1/content-items');

    const token = getAccessToken();
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);

    xhr.upload.onprogress = (evt) => {
      if (evt.lengthComputable) setProgress(Math.round((evt.loaded / evt.total) * 100));
    };

    xhr.onload = () => {
      setUploading(false);
      if (xhr.status >= 200 && xhr.status < 300) {
        setSuccess(true);
        setTitle('');
        setDescription('');
        setFile(null);
      } else {
        onError(t('app.error'));
      }
    };
    xhr.onerror = () => {
      setUploading(false);
      onError(t('app.error'));
    };

    xhr.send(formData);
  }

  if (success) {
    return (
      <div className="card" style={{ padding: 20, maxWidth: 500 }}>
        <h3 style={{ color: 'var(--color-success)', marginBottom: 12 }}>{t('teacherContent.uploadSuccess')}</h3>
        <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 16 }}>{t('teacherContent.uploadSuccessMsg')}</p>
        <button className="btn btn-primary" onClick={() => setSuccess(false)}>
          {t('teacherContent.uploadAnother')}
        </button>
      </div>
    );
  }

  return (
    <form className="card" style={{ padding: 20, maxWidth: 500 }} onSubmit={handleSubmit}>
      <h3 style={{ margin: '0 0 16px' }}>{t('teacherContent.uploadTitle')}</h3>

      <div className="form-field" style={{ marginBottom: 12 }}>
        <label>{t('teacherContent.contentTitle')}</label>
        <input className="filter-input" value={title} onChange={(e) => setTitle(e.target.value)} required style={{ width: '100%' }} />
      </div>
      <div className="form-field" style={{ marginBottom: 12 }}>
        <label>{t('teacherContent.description')}</label>
        <input className="filter-input" value={description} onChange={(e) => setDescription(e.target.value)} style={{ width: '100%' }} />
      </div>
      <div className="form-field" style={{ marginBottom: 12 }}>
        <label>{t('teacherContent.contentType')}</label>
        <select className="filter-select" value={contentType} onChange={(e) => setContentType(e.target.value)} style={{ width: '100%' }}>
          <option value="pdf">{t('cms.contentTypes.pdf')}</option>
          <option value="video">{t('cms.contentTypes.video')}</option>
          <option value="audio">{t('cms.contentTypes.audio')}</option>
          <option value="interactive">{t('cms.contentTypes.interactive')}</option>
        </select>
      </div>
      <div className="form-field" style={{ marginBottom: 12 }}>
        <label>{t('teacherContent.subject')}</label>
        <select className="filter-select" value={subject} onChange={(e) => setSubject(e.target.value)} style={{ width: '100%' }}>
          <option value="">{t('teacherContent.allSubjects')}</option>
          {['math', 'french', 'arabic', 'science', 'history', 'geography', 'english'].map((s) => (
            <option key={s} value={s}>{t(`cms.subjects.${s}`, s)}</option>
          ))}
        </select>
      </div>
      <div className="form-field" style={{ marginBottom: 12 }}>
        <label>{t('teacherContent.level')}</label>
        <select className="filter-select" value={levelBand} onChange={(e) => setLevelBand(e.target.value)} style={{ width: '100%' }}>
          <option value="">{t('teacherContent.allLevels')}</option>
          <option value="primaire">Primaire</option>
          <option value="college">College</option>
          <option value="lycee">Lycee</option>
        </select>
      </div>
      <div className="form-field" style={{ marginBottom: 12 }}>
        <label>{t('teacherContent.file')}</label>
        <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} required />
      </div>

      {uploading && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 4 }}>{t('teacherContent.uploading')} {progress}%</div>
          <div style={{ height: 6, background: 'var(--color-bg-secondary)', borderRadius: 3 }}>
            <div style={{ height: '100%', borderRadius: 3, background: 'var(--color-primary)', width: `${progress}%`, transition: 'width 0.3s' }} />
          </div>
        </div>
      )}

      <button type="submit" className="btn btn-primary" disabled={uploading || !title.trim() || !file}>
        {uploading ? t('app.loading') : t('teacherContent.upload')}
      </button>
    </form>
  );
}

/* ================================================================== */
/* My Submissions Tab                                                  */
/* ================================================================== */
function SubmissionsTab({ onError }: { onError: (e: string | null) => void }) {
  const { t } = useTranslation();
  const [items, setItems] = useState<MySubmission[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('');

  const fetchSubmissions = useCallback(async () => {
    try {
      const params: Record<string, string | number | undefined> = {};
      if (filterStatus) params.status = filterStatus;
      const resp = await api.list<MySubmission>('/content/my-submissions', params);
      setItems(resp.data);
      onError(null);
    } catch (err) {
      onError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [filterStatus, onError, t]);

  useEffect(() => {
    setLoading(true);
    fetchSubmissions().finally(() => setLoading(false));
  }, [fetchSubmissions]);

  if (loading) return <LoadingState />;

  const statusColors: Record<string, string> = {
    PENDING: 'var(--color-warning)',
    UNDER_REVIEW: 'var(--color-info, #2196f3)',
    APPROVED: 'var(--color-success)',
    REJECTED: 'var(--color-error)',
  };

  return (
    <>
      <div className="filters-bar" style={{ marginBottom: 16 }}>
        <select className="filter-select" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="">{t('teacherContent.allStatuses')}</option>
          {['PENDING', 'UNDER_REVIEW', 'APPROVED', 'REJECTED'].map((s) => (
            <option key={s} value={s}>{t(`cms.reviewStatuses.${s}`)}</option>
          ))}
        </select>
      </div>

      {items.length === 0 ? (
        <EmptyState message={t('teacherContent.noSubmissions')} />
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('teacherContent.contentTitle')}</th>
                <th>{t('teacherContent.submissionStatus')}</th>
                <th>{t('teacherContent.submittedAt')}</th>
                <th>{t('teacherContent.feedback')}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((sub) => (
                <tr key={sub.id}>
                  <td style={{ fontWeight: 600 }}>{sub.content_title}</td>
                  <td>
                    <span style={{ color: statusColors[sub.status] || 'inherit', fontWeight: 600, fontSize: 13 }}>
                      {t(`cms.reviewStatuses.${sub.status}`, sub.status)}
                    </span>
                  </td>
                  <td style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
                    {sub.submitted_at ? new Date(sub.submitted_at).toLocaleDateString() : '—'}
                  </td>
                  <td style={{ fontSize: 13 }}>
                    {sub.review_notes || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
