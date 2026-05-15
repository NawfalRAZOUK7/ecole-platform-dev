import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/app/providers/AuthContext';
import { Badge } from '@/shared/ui/Badge';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { formatDate } from '@/shared/i18n';
import {
  useDocumentsOptions,
  useStudentChecklist,
  useStudentDocuments,
  useUploadStudentDocument,
} from '../model/useDocuments';
import { humanSize, openSignedUrl } from '../lib/documents.utils';
import type { ChecklistItem } from '../api/documents.api';

const STATUS_VARIANT: Record<ChecklistItem['status'], 'success' | 'warning' | 'error'> = {
  uploaded: 'success',
  missing: 'warning',
  expired: 'error',
};

export function StudentDocumentsPage() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const uploadXhrRef = useRef<{ abort: () => void } | null>(null);

  const isStudent = user?.role === 'STD';
  const isParent = user?.role === 'PAR';
  const canSelectStudent = ['ADM', 'DIR', 'TCH'].includes(user?.role ?? '');

  const optionsQuery = useDocumentsOptions();
  const options = optionsQuery.data ?? { students: [], categories: [] };

  const [selectedStudentId, setSelectedStudentId] = useState(isStudent ? (user?.id ?? '') : '');
  const [uploadCategory, setUploadCategory] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadingFor, setUploadingFor] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const checklistQuery = useStudentChecklist(selectedStudentId);
  const documentsQuery = useStudentDocuments(selectedStudentId);
  const uploadMutation = useUploadStudentDocument();

  const checklist = checklistQuery.data ?? [];
  const documents = documentsQuery.data ?? [];

  useEffect(() => {
    if (!selectedStudentId && options.students.length > 0 && canSelectStudent) {
      setSelectedStudentId(options.students[0].id);
    }
    if (!uploadCategory && options.categories.length > 0) {
      setUploadCategory(options.categories[0]);
    }
  }, [options, selectedStudentId, canSelectStudent, uploadCategory]);

  async function handleUpload(category?: string) {
    if (!uploadFile || !selectedStudentId) return;
    setError(null);
    const cat = category ?? uploadCategory;
    try {
      await uploadMutation.mutateAsync({
        studentId: selectedStudentId,
        payload: { file: uploadFile, category: cat, language: i18n.language || 'fr' },
        onProgress: setUploadProgress,
        onRequestCreated: (xhr) => {
          uploadXhrRef.current = xhr;
        },
      });
      setUploadFile(null);
      setUploadingFor(null);
      setUploadProgress(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    } finally {
      uploadXhrRef.current = null;
    }
  }

  if (optionsQuery.isLoading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('documents.studentDocuments.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      {canSelectStudent && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="form-field" style={{ marginBottom: 0 }}>
            <label>{t('documents.studentSelector')}</label>
            <select
              className="filter-select"
              value={selectedStudentId}
              onChange={(e) => setSelectedStudentId(e.target.value)}
            >
              <option value="">{t('documents.studentDocuments.selectStudent')}</option>
              {options.students.map((student) => (
                <option key={student.id} value={student.id}>
                  {student.full_name}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {!isStudent && !isParent && !selectedStudentId ? (
        <EmptyState message={t('documents.studentDocuments.selectStudent')} icon="👤" />
      ) : checklistQuery.isLoading || documentsQuery.isLoading ? (
        <LoadingState />
      ) : (
        <>
          {checklist.length > 0 && (
            <div className="card" style={{ marginBottom: 20 }}>
              <h2 style={{ marginBottom: 16 }}>{t('documents.studentDocuments.checklist')}</h2>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>{t('documents.categories.other')}</th>
                    <th>
                      {t('documents.checklist.uploaded')}/{t('documents.checklist.missing')}
                    </th>
                    <th>{t('documents.expiresAt')}</th>
                    <th>{t('app.actions')}</th>
                  </tr>
                </thead>
                <tbody>
                  {checklist.map((item) => (
                    <tr key={item.category}>
                      <td>
                        <div>
                          <strong>
                            {t(`documents.categories.${item.category}`, item.category)}
                          </strong>
                          {item.description && (
                            <p
                              style={{
                                fontSize: 12,
                                color: 'var(--color-text-secondary)',
                                margin: 0,
                              }}
                            >
                              {item.description}
                            </p>
                          )}
                          {item.required && (
                            <span style={{ fontSize: 11, color: 'var(--color-error)' }}>
                              {t('documents.studentDocuments.required')}
                            </span>
                          )}
                        </div>
                      </td>
                      <td>
                        <Badge variant={STATUS_VARIANT[item.status]}>
                          {t(`documents.checklist.${item.status}`)}
                        </Badge>
                      </td>
                      <td>{item.expires_at ? formatDate(item.expires_at, i18n.language) : '—'}</td>
                      <td>
                        <div style={{ display: 'flex', gap: 8 }}>
                          {item.document?.download_url && (
                            <button
                              type="button"
                              className="btn btn-sm btn-secondary"
                              onClick={() => openSignedUrl(item.document?.download_url ?? null)}
                            >
                              {t('documents.download')}
                            </button>
                          )}
                          {(item.status === 'missing' || item.status === 'expired') && (
                            <button
                              type="button"
                              className="btn btn-sm btn-primary"
                              onClick={() => setUploadingFor(item.category)}
                            >
                              {t('documents.uploadTitle')}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="card" style={{ marginBottom: 20 }}>
            <h2 style={{ marginBottom: 16 }}>{t('documents.tabs.student')}</h2>
            {documents.length === 0 ? (
              <EmptyState message={t('documents.empty')} icon="📄" />
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>{t('documents.studentDocuments.filename')}</th>
                    <th>{t('documents.categories.other')}</th>
                    <th>{t('documents.studentDocuments.size')}</th>
                    <th>{t('documents.expiresAt')}</th>
                    <th>{t('app.actions')}</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc) => (
                    <tr key={doc.id}>
                      <td>{doc.original_filename}</td>
                      <td>{t(`documents.categories.${doc.category}`, doc.category)}</td>
                      <td>{humanSize(doc.size_bytes)}</td>
                      <td>
                        {doc.expires_at ? (
                          <span
                            style={{ color: doc.is_expired ? 'var(--color-error)' : 'inherit' }}
                          >
                            {formatDate(doc.expires_at, i18n.language)}
                          </span>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td>
                        <button
                          type="button"
                          className="btn btn-sm btn-secondary"
                          onClick={() => openSignedUrl(doc.download_url)}
                        >
                          {t('documents.download')}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="card">
            <h2 style={{ marginBottom: 16 }}>{t('documents.uploadTitle')}</h2>
            <div className="form-field">
              <label>{t('documents.studentDocuments.category')}</label>
              <select
                className="filter-select"
                value={uploadCategory}
                onChange={(e) => setUploadCategory(e.target.value)}
              >
                {options.categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {t(`documents.categories.${cat}`, cat)}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-field">
              <label>{t('documents.studentDocuments.file')}</label>
              <input type="file" onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)} />
            </div>
            {uploadProgress > 0 && uploadProgress < 100 && (
              <div style={{ marginBottom: 12 }}>
                <div style={{ height: 8, background: 'var(--color-surface-2)', borderRadius: 4 }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${uploadProgress}%`,
                      background: 'var(--color-primary)',
                      borderRadius: 4,
                      transition: 'width 0.2s',
                    }}
                  />
                </div>
                <p style={{ fontSize: 12, marginTop: 4 }}>{uploadProgress}%</p>
              </div>
            )}
            <div style={{ display: 'flex', gap: 12 }}>
              <button
                type="button"
                className="btn btn-primary"
                disabled={!uploadFile || !selectedStudentId || uploadMutation.isPending}
                onClick={() => void handleUpload()}
              >
                {uploadMutation.isPending ? t('documents.uploading') : t('documents.uploadAction')}
              </button>
              {uploadMutation.isPending && (
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => uploadXhrRef.current?.abort()}
                >
                  {t('documents.cancelUpload')}
                </button>
              )}
            </div>
          </div>
        </>
      )}

      {uploadingFor && (
        <div className="modal-overlay" onClick={() => setUploadingFor(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ marginBottom: 12 }}>
              {t('documents.uploadTitle')} —{' '}
              {t(`documents.categories.${uploadingFor}`, uploadingFor)}
            </h2>
            <div className="form-field">
              <input type="file" onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)} />
            </div>
            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <button
                type="button"
                className="btn btn-primary"
                disabled={!uploadFile || uploadMutation.isPending}
                onClick={() => void handleUpload(uploadingFor)}
              >
                {uploadMutation.isPending ? t('documents.uploading') : t('documents.uploadAction')}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => {
                  setUploadingFor(null);
                  setUploadFile(null);
                }}
              >
                {t('app.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
