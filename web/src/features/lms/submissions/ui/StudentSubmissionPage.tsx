/**
 * Student submission page — select assignment, upload files, submit.
 *
 * Reference: Phase 4C (from 3B) — Student submission with file upload
 * Phase 10B — PDF exercise workflow: download exercise PDF, upload solution scan/photo.
 * Flow: Select assignment → Create submission (POST /submissions) → Upload files → Done.
 * PRINTABLE_PDF: Download exercise → Upload solution → Finalize (POST /submissions/{id}/submit).
 */

import { useMemo, useState, type FormEvent, type MouseEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { useSignedUrl } from '@/shared/hooks/useSignedUrl';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { FileUpload } from '@/shared/ui/FileUpload';
import { toBannerError } from '@/shared/ui/errorUtils';
import {
  useCreateStudentSubmission,
  useFinalizeStudentSubmission,
  useSubmissionAssignments,
  useUploadSubmissionFile,
} from '../model/useSubmissions';
import type { AssignmentOption } from '../api/submissions.api';

type SubmitStep = 'select' | 'uploading' | 'done';

export function StudentSubmissionPage() {
  const { t } = useTranslation();
  const [selectedAssignmentId, setSelectedAssignmentId] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [step, setStep] = useState<SubmitStep>('select');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [localError, setLocalError] = useState<string | null>(null);
  const assignmentsQuery = useSubmissionAssignments();
  const createSubmissionMutation = useCreateStudentSubmission();
  const uploadFileMutation = useUploadSubmissionFile();
  const finalizeSubmissionMutation = useFinalizeStudentSubmission();
  const assignments: AssignmentOption[] = useMemo(
    () => assignmentsQuery.data ?? [],
    [assignmentsQuery.data],
  );
  const selectedAssignment = assignments.find(
    (assignment) => assignment.id === selectedAssignmentId,
  );
  const exercisePdfPath =
    selectedAssignment?.exercise_type === 'PRINTABLE_PDF' && selectedAssignment.exercise_pdf_path
      ? `/assignments/${selectedAssignment.id}/exercise-pdf`
      : null;
  const exercisePdfUrl = useSignedUrl(exercisePdfPath);
  const dismissibleError = useDismissibleError(
    useMemo(
      () =>
        localError ||
        toBannerError(
          assignmentsQuery.error ??
            createSubmissionMutation.error ??
            uploadFileMutation.error ??
            finalizeSubmissionMutation.error ??
            exercisePdfUrl.error,
          t('app.error'),
        ),
      [
        assignmentsQuery.error,
        createSubmissionMutation.error,
        exercisePdfUrl.error,
        finalizeSubmissionMutation.error,
        localError,
        t,
        uploadFileMutation.error,
      ],
    ),
  );

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!selectedAssignmentId) {
      return;
    }

    setLocalError(null);
    setStep('uploading');
    setUploadProgress(0);

    try {
      const submission = await createSubmissionMutation.mutateAsync(selectedAssignmentId);
      const submissionId = submission.id;
      const isPrintablePdf = selectedAssignment?.exercise_type === 'PRINTABLE_PDF';

      for (let index = 0; index < files.length; index += 1) {
        const file = files[index];
        const fileTypeHint = isPrintablePdf
          ? file.type?.startsWith('image/')
            ? 'SOLUTION_PHOTO'
            : 'SOLUTION_SCAN'
          : undefined;

        await uploadFileMutation.mutateAsync({
          submissionId,
          file,
          fileTypeHint,
        });
        setUploadProgress(index + 1);
      }

      if (isPrintablePdf) {
        await finalizeSubmissionMutation.mutateAsync(submissionId);
      }

      setStep('done');
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : t('app.error'));
      setStep('select');
    }
  }

  function triggerExercisePdfDownload(url: string, filename: string) {
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
  }

  async function handleExercisePdfClick(event: MouseEvent<HTMLAnchorElement>) {
    if (!exercisePdfUrl.url || exercisePdfUrl.isExpired) {
      event.preventDefault();
      const metadata = await exercisePdfUrl.refresh();
      if (metadata) {
        triggerExercisePdfDownload(
          metadata.download_url,
          metadata.filename || `exercise_${selectedAssignment?.id ?? 'assignment'}.pdf`,
        );
      }
    }
  }

  function handleReset() {
    setSelectedAssignmentId('');
    setFiles([]);
    setStep('select');
    setUploadProgress(0);
    setLocalError(null);
  }

  if (assignmentsQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('studentSubmission.title')}</h1>

      <ErrorBanner error={dismissibleError.error} onDismiss={dismissibleError.dismiss} />

      {step === 'done' && (
        <div className="card" style={{ maxWidth: 500 }}>
          <h3
            style={{
              color: 'var(--color-success)',
              marginBottom: 12,
              fontSize: 16,
              fontWeight: 600,
            }}
          >
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
            <form onSubmit={(event) => void handleSubmit(event)}>
              <div className="card" style={{ maxWidth: 600 }}>
                <div className="form-field" style={{ marginBottom: 16 }}>
                  <label>{t('studentSubmission.selectAssignment')}</label>
                  <select
                    className="filter-select"
                    value={selectedAssignmentId}
                    onChange={(event) => setSelectedAssignmentId(event.target.value)}
                    disabled={createSubmissionMutation.isPending || uploadFileMutation.isPending}
                    required
                    style={{ width: '100%' }}
                  >
                    <option value="">{t('studentSubmission.choosePlaceholder')}</option>
                    {assignments.map((assignment) => (
                      <option key={assignment.id} value={assignment.id}>
                        {assignment.title} ({assignment.total_points} pts)
                      </option>
                    ))}
                  </select>
                </div>

                {selectedAssignment && (
                  <div
                    style={{
                      marginBottom: 16,
                      padding: 12,
                      background: 'var(--color-bg)',
                      borderRadius: 'var(--radius)',
                      fontSize: 13,
                    }}
                  >
                    <div>
                      <strong>{selectedAssignment.title}</strong>
                    </div>
                    {selectedAssignment.exercise_type &&
                      selectedAssignment.exercise_type !== 'STANDARD' && (
                        <div
                          style={{ color: 'var(--color-primary)', marginTop: 4, fontWeight: 600 }}
                        >
                          {t(
                            `studentSubmission.exerciseType_${selectedAssignment.exercise_type}`,
                            selectedAssignment.exercise_type,
                          )}
                        </div>
                      )}
                    {selectedAssignment.due_at && (
                      <div style={{ color: 'var(--color-text-secondary)', marginTop: 4 }}>
                        {t('studentSubmission.dueAt')}:{' '}
                        {new Date(selectedAssignment.due_at).toLocaleString()}
                      </div>
                    )}
                    <div style={{ color: 'var(--color-text-secondary)', marginTop: 2 }}>
                      {t('studentSubmission.points')}: {selectedAssignment.total_points}
                    </div>
                  </div>
                )}

                {selectedAssignment?.exercise_type === 'PRINTABLE_PDF' &&
                  selectedAssignment.exercise_pdf_path && (
                    <div
                      style={{
                        marginBottom: 16,
                        padding: 12,
                        background: 'var(--color-bg)',
                        borderRadius: 'var(--radius)',
                        border: '1px solid var(--color-primary)',
                      }}
                    >
                      <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>
                        {t('studentSubmission.pdfExercise')}
                      </div>
                      <p
                        style={{
                          fontSize: 12,
                          color: 'var(--color-text-secondary)',
                          margin: '0 0 8px',
                        }}
                      >
                        {t('studentSubmission.pdfInstructions')}
                      </p>
                      <a
                        href={exercisePdfUrl.url ?? '#'}
                        download={
                          exercisePdfUrl.filename ?? `exercise_${selectedAssignment.id}.pdf`
                        }
                        className="btn btn-primary"
                        style={{ fontSize: 12 }}
                        onClick={(event) => void handleExercisePdfClick(event)}
                        aria-disabled={exercisePdfUrl.isFetching && !exercisePdfUrl.url}
                      >
                        {exercisePdfUrl.isFetching && !exercisePdfUrl.url
                          ? t('app.loading')
                          : t('studentSubmission.downloadPdf')}
                      </a>
                    </div>
                  )}

                <div className="form-field" style={{ marginBottom: 16 }}>
                  <label>{t('studentSubmission.attachFiles')}</label>
                  <FileUpload
                    onFilesSelected={setFiles}
                    accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg,.zip"
                    maxFiles={5}
                    maxSizeMb={25}
                    disabled={createSubmissionMutation.isPending || uploadFileMutation.isPending}
                  />
                </div>

                {step === 'uploading' && files.length > 0 && (
                  <div style={{ marginBottom: 16 }}>
                    <div
                      style={{
                        fontSize: 13,
                        color: 'var(--color-text-secondary)',
                        marginBottom: 4,
                      }}
                    >
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

                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={
                    createSubmissionMutation.isPending ||
                    uploadFileMutation.isPending ||
                    !selectedAssignmentId
                  }
                >
                  {createSubmissionMutation.isPending || uploadFileMutation.isPending
                    ? t('app.loading')
                    : t('studentSubmission.submit')}
                </button>
              </div>
            </form>
          )}
        </>
      )}
    </div>
  );
}
