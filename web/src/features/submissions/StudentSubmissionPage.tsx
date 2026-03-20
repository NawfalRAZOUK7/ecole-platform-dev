/**
 * Student submission page — select assignment, upload files, submit.
 *
 * Reference: Phase 4C (from 3B) — Student submission with file upload
 * Flow: Select assignment → Create submission (POST /submissions) → Upload files → Done.
 */

import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError, getAccessToken } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';
import { FileUpload } from '@/shared/ui/FileUpload';

interface AssignmentOption {
  id: string;
  title: string;
  course_id: string;
  due_at: string | null;
  total_points: number;
}

type SubmitStep = 'select' | 'uploading' | 'done';

export function StudentSubmissionPage() {
  const { t } = useTranslation();
  const [assignments, setAssignments] = useState<AssignmentOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedAssignmentId, setSelectedAssignmentId] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [step, setStep] = useState<SubmitStep>('select');
  const [submitting, setSubmitting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const fetchAssignments = useCallback(async () => {
    try {
      const resp = await api.list<AssignmentOption>('/assignments');
      setAssignments(resp.data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [t]);

  useEffect(() => {
    setLoading(true);
    fetchAssignments().finally(() => setLoading(false));
  }, [fetchAssignments]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!selectedAssignmentId) return;
    setSubmitting(true);
    setError(null);
    setStep('uploading');

    try {
      // 1. Create submission
      const resp = await api.post<{ id: string }>('/submissions', {
        assignment_id: selectedAssignmentId,
      });
      const submissionId = resp.data.id;

      // 2. Upload files one by one
      for (let i = 0; i < files.length; i++) {
        const formData = new FormData();
        formData.append('file', files[i]);

        const token = getAccessToken();
        const headers: Record<string, string> = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;

        await fetch(`/api/v1/submissions/${submissionId}/files`, {
          method: 'POST',
          credentials: 'include',
          headers,
          body: formData,
        });
        setUploadProgress(i + 1);
      }

      setStep('done');
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
      setStep('select');
    } finally {
      setSubmitting(false);
    }
  }

  function handleReset() {
    setSelectedAssignmentId('');
    setFiles([]);
    setStep('select');
    setUploadProgress(0);
    setError(null);
  }

  if (loading) return <LoadingState />;

  const selectedAssignment = assignments.find((a) => a.id === selectedAssignmentId);

  return (
    <div className="page">
      <h1 className="page-title">{t('studentSubmission.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      {step === 'done' && (
        <div className="card" style={{ maxWidth: 500 }}>
          <h3 style={{ color: 'var(--color-success)', marginBottom: 12, fontSize: 16, fontWeight: 600 }}>
            {t('studentSubmission.success')}
          </h3>
          <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', marginBottom: 16 }}>
            {t('studentSubmission.successMessage')}
          </p>
          <button className="btn btn-primary" onClick={handleReset}>
            {t('studentSubmission.submitAnother')}
          </button>
        </div>
      )}

      {step !== 'done' && (
        <>
          {assignments.length === 0 ? (
            <EmptyState message={t('studentSubmission.noAssignments')} />
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="card" style={{ maxWidth: 600 }}>
                {/* Assignment selection */}
                <div className="form-field" style={{ marginBottom: 16 }}>
                  <label>{t('studentSubmission.selectAssignment')}</label>
                  <select
                    className="filter-select"
                    value={selectedAssignmentId}
                    onChange={(e) => setSelectedAssignmentId(e.target.value)}
                    disabled={submitting}
                    required
                    style={{ width: '100%' }}
                  >
                    <option value="">{t('studentSubmission.choosePlaceholder')}</option>
                    {assignments.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.title} ({a.total_points} pts)
                      </option>
                    ))}
                  </select>
                </div>

                {/* Assignment info */}
                {selectedAssignment && (
                  <div style={{ marginBottom: 16, padding: 12, background: 'var(--color-bg)', borderRadius: 'var(--radius)', fontSize: 13 }}>
                    <div><strong>{selectedAssignment.title}</strong></div>
                    {selectedAssignment.due_at && (
                      <div style={{ color: 'var(--color-text-secondary)', marginTop: 4 }}>
                        {t('studentSubmission.dueAt')}: {new Date(selectedAssignment.due_at).toLocaleString()}
                      </div>
                    )}
                    <div style={{ color: 'var(--color-text-secondary)', marginTop: 2 }}>
                      {t('studentSubmission.points')}: {selectedAssignment.total_points}
                    </div>
                  </div>
                )}

                {/* File upload */}
                <div className="form-field" style={{ marginBottom: 16 }}>
                  <label>{t('studentSubmission.attachFiles')}</label>
                  <FileUpload
                    onFilesSelected={setFiles}
                    accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg,.zip"
                    maxFiles={5}
                    maxSizeMb={25}
                    disabled={submitting}
                  />
                </div>

                {/* Upload progress */}
                {step === 'uploading' && files.length > 0 && (
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 4 }}>
                      {t('studentSubmission.uploading')} ({uploadProgress}/{files.length})
                    </div>
                    <div style={{ height: 4, background: 'var(--color-border)', borderRadius: 2 }}>
                      <div
                        style={{
                          height: '100%',
                          width: `${(uploadProgress / files.length) * 100}%`,
                          background: 'var(--color-primary)',
                          borderRadius: 2,
                          transition: 'width 0.3s',
                        }}
                      />
                    </div>
                  </div>
                )}

                {/* Submit */}
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={submitting || !selectedAssignmentId}
                >
                  {submitting ? t('app.loading') : t('studentSubmission.submit')}
                </button>
              </div>
            </form>
          )}
        </>
      )}
    </div>
  );
}

