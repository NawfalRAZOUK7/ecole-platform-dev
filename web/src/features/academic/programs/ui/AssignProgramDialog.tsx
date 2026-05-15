/**
 * AssignProgramDialog — modal form for assigning / changing the program
 * (filière) on an enrollment. Calls POST /enrollments/:enrollmentId/program
 * via the useAssignProgramMutation hook.
 *
 * Surfacing rules:
 *   - 409 ConflictError ("Enrollment already assigned to this program") and
 *     ("Program is not active") render in the dialog's error banner.
 *   - 422 ValidationError on bad reason_code shouldn't reach here (the radio
 *     buttons restrict input) but is handled defensively anyway.
 */

import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { ApiClientError } from '@/core/api/client';
import { ErrorBanner, toBannerError } from '@/shared/ui';
import {
  useAssignProgramMutation,
  useProgramsQuery,
  useProgramVersionsQuery,
} from '../model/usePrograms';
import type { Program, ProgramAssignmentReason } from '../api/programs.api';

const REASON_CODES: ProgramAssignmentReason[] = [
  'INITIAL',
  'TRANSFER',
  'PROMOTION',
  'CORRECTION',
  'READMISSION',
];

interface AssignProgramDialogProps {
  readonly open: boolean;
  readonly enrollmentId: string;
  /** When provided, the success handler invalidates this student's history. */
  readonly studentId?: string;
  /** Pre-fill from an existing enrollment.program_id, if known. */
  readonly currentProgramId?: string | null;
  readonly onClose: () => void;
  readonly onAssigned?: (eventId: string) => void;
}

export function AssignProgramDialog({
  open,
  enrollmentId,
  studentId,
  currentProgramId,
  onClose,
  onAssigned,
}: AssignProgramDialogProps) {
  const { t } = useTranslation();
  const programsQuery = useProgramsQuery(true, open); // active only
  const assignMutation = useAssignProgramMutation();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  const [programId, setProgramId] = useState<string>('');
  const [programVersionId, setProgramVersionId] = useState<string>('');
  const [reasonCode, setReasonCode] = useState<ProgramAssignmentReason>('INITIAL');
  const [reasonNote, setReasonNote] = useState('');

  // Versions for the *currently selected* program (Phase 3.1).
  const versionsQuery = useProgramVersionsQuery(programId || undefined);

  // Reset form whenever the dialog re-opens
  useEffect(() => {
    if (!open) {
      return;
    }
    setProgramId('');
    setProgramVersionId('');
    setReasonCode(currentProgramId ? 'TRANSFER' : 'INITIAL');
    setReasonNote('');
    assignMutation.reset();
  }, [open, currentProgramId, assignMutation]);

  // When the selected program changes, reset the version selection.
  useEffect(() => {
    setProgramVersionId('');
  }, [programId]);

  // Focus management — same pattern as ConfirmDialog
  useEffect(() => {
    if (!open) {
      previousFocusRef.current?.focus();
      return undefined;
    }
    previousFocusRef.current =
      document.activeElement instanceof HTMLElement ? document.activeElement : null;
    dialogRef.current?.querySelector<HTMLElement>('select, button')?.focus();

    function handleKey(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
      }
    }
    globalThis.addEventListener('keydown', handleKey);
    return () => globalThis.removeEventListener('keydown', handleKey);
  }, [open, onClose]);

  const error = useMemo(
    () => toBannerError(assignMutation.error, t('app.error')),
    [assignMutation.error, t],
  );

  // Filter out the program already on the enrollment so the user can't pick a
  // no-op (the backend would 409, but UX is better if we hide the option).
  const programs = useMemo<Program[]>(() => {
    const list = programsQuery.data ?? [];
    if (!currentProgramId) {
      return list;
    }
    return list.filter((p) => p.id !== currentProgramId);
  }, [programsQuery.data, currentProgramId]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!programId) {
      return;
    }
    try {
      const result = await assignMutation.mutateAsync({
        enrollmentId,
        body: {
          program_id: programId,
          program_version_id: programVersionId || null,
          reason_code: reasonCode,
          reason_note: reasonNote.trim() || null,
        },
        studentId,
      });
      onAssigned?.(result.id);
      onClose();
    } catch (err) {
      // 409 / 422 surface inline in the ErrorBanner via assignMutation.error.
      // We rethrow only unexpected errors.
      if (!(err instanceof ApiClientError)) {
        throw err;
      }
    }
  }

  if (!open) {
    return null;
  }

  return (
    <dialog
      ref={dialogRef}
      className="confirm-dialog__overlay"
      open
      aria-labelledby="assign-program-title"
    >
      <button
        type="button"
        className="confirm-dialog__backdrop"
        aria-label={t('app.close', { defaultValue: 'Close dialog' })}
        tabIndex={-1}
        onClick={onClose}
      />
      <div className="confirm-dialog">
        <form
          className="confirm-dialog__content confirm-dialog__content--info"
          onSubmit={handleSubmit}
        >
          <h2 id="assign-program-title">{t('admin.programs.assign.title')}</h2>
          <p>{t('admin.programs.assign.subtitle')}</p>

          <ErrorBanner error={error} onDismiss={() => assignMutation.reset()} />

          <div className="form-field">
            <label htmlFor="assign-program-select">{t('admin.programs.assign.programLabel')}</label>
            <select
              id="assign-program-select"
              className="filter-select"
              value={programId}
              onChange={(e) => setProgramId(e.target.value)}
              required
            >
              <option value="">{t('admin.programs.assign.programPlaceholder')}</option>
              {programs.map((program) => (
                <option key={program.id} value={program.id}>
                  {program.code} — {program.name} (v{program.version_label})
                </option>
              ))}
            </select>
          </div>

          {programId && (versionsQuery.data?.length ?? 0) > 0 && (
            <div className="form-field">
              <label htmlFor="assign-program-version-select">
                {t('admin.programs.assign.versionLabel', {
                  defaultValue: 'Curriculum version (optional)',
                })}
              </label>
              <select
                id="assign-program-version-select"
                className="filter-select"
                value={programVersionId}
                onChange={(e) => setProgramVersionId(e.target.value)}
              >
                <option value="">
                  {t('admin.programs.assign.versionPlaceholder', {
                    defaultValue: '(no specific version)',
                  })}
                </option>
                {(versionsQuery.data ?? []).map((version) => (
                  <option key={version.id} value={version.id} disabled={!version.is_active}>
                    v{version.version_label}
                    {version.is_active ? '' : ' (inactive)'}
                    {version.effective_from ? ` — from ${version.effective_from}` : ''}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="form-field">
            <span className="form-field__legend">{t('admin.programs.assign.reasonLabel')}</span>
            <div role="radiogroup" aria-label={t('admin.programs.assign.reasonLabel')}>
              {REASON_CODES.map((code) => (
                <label
                  key={code}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 4,
                    marginInlineEnd: 12,
                  }}
                >
                  <input
                    type="radio"
                    name="reason_code"
                    value={code}
                    checked={reasonCode === code}
                    onChange={() => setReasonCode(code)}
                  />
                  {t(`admin.programs.assign.reason.${code}`, code)}
                </label>
              ))}
            </div>
          </div>

          <div className="form-field">
            <label htmlFor="assign-program-note">{t('admin.programs.assign.noteLabel')}</label>
            <textarea
              id="assign-program-note"
              className="input"
              rows={3}
              maxLength={2000}
              value={reasonNote}
              onChange={(e) => setReasonNote(e.target.value)}
              placeholder={t('admin.programs.assign.notePlaceholder')}
            />
          </div>

          <div className="confirm-dialog__actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              {t('app.cancel')}
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!programId || assignMutation.isPending}
              aria-busy={assignMutation.isPending ? 'true' : 'false'}
            >
              {assignMutation.isPending ? t('app.loading') : t('admin.programs.assign.submit')}
            </button>
          </div>
        </form>
      </div>
    </dialog>
  );
}
