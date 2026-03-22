/**
 * Student submission page — select assignment, upload files, submit.
 *
 * Reference: Phase 4C (from 3B) — Student submission with file upload
 * Phase 10B — PDF exercise workflow: download exercise PDF, upload solution scan/photo.
 * Flow: Select assignment → Create submission (POST /submissions) → Upload files → Done.
 * PRINTABLE_PDF: Download exercise → Upload solution → Finalize (POST /submissions/{id}/submit).
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
  exercise_type?: string;
  exercise_pdf_path?: string | null;
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
      const isPrintablePdf = selectedAssignment?.exercise_type === 'PRINTABLE_PDF';
      for (let i = 0; i < files.length; i++) {
        const formData = new FormData();
        formData.append('file', files[i]);
        // Phase 10B: add file_type_hint for PRINTABLE_PDF submissions
        if (isPrintablePdf) {
          const hint = files[i].type?.startsWith('image/') ? 'SOLUTION_PHOTO' : 'SOLUTION_SCAN';
          formData.append('file_type_hint', hint);
        }

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

      // Phase 10B: finalize PRINTABLE_PDF draft submission
      if (isPrintablePdf) {
        await api.post(`/submissions/${submissionId}/submit`);
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
                    {selectedAssignment.exercise_type && selectedAssignment.exercise_type !== 'STANDARD' && (
                      <div style={{ color: 'var(--color-primary)', marginTop: 4, fontWeight: 600 }}>
                        {t(`studentSubmission.exerciseType_${selectedAssignment.exercise_type}`, selectedAssignment.exercise_type)}
                      </div>
                    )}
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

                {/* Phase 10B: PDF exercise download */}
                {selectedAssignment?.exercise_type === 'PRINTABLE_PDF' && selectedAssignment.exercise_pdf_path && (
                  <div style={{ marginBottom: 16, padding: 12, background: 'var(--color-bg)', borderRadius: 'var(--radius)', border: '1px solid var(--color-primary)' }}>
                    <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>
                      {t('studentSubmission.pdfExercise')}
                    </div>
                    <p style={{ fontSize: 12, color: 'var(--color-text-secondary)', margin: '0 0 8px' }}>
                      {t('studentSubmission.pdfInstructions')}
                    </p>
                    <a
                      href={`/api/v1/assignments/${selectedAssignment.id}/exercise-pdf`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-primary"
                      style={{ fontSize: 12, textDecoration: 'none', display: 'inline-block' }}
                      onClick={(e) => {
                        // Attach auth header via fetch download
                        e.preventDefault();
                        const token = getAccessToken();
                        fetch(`/api/v1/assignments/${selectedAssignment.id}/exercise-pdf`, {
                          headers: token ? { Authorization: `Bearer ${token}` } : {},
                          credentials: 'include',
                        })
                          .then((r) => r.blob())
                          .then((blob) => {
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `exercise_${selectedAssignment.id}.pdf`;
                            a.click();
                            URL.revokeObjectURL(url);
                          });
                      }}
                    >
                      {t('studentSubmission.downloadPdf')}
                    </a>
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

