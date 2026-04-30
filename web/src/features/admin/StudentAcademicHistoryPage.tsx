/**
 * StudentAcademicHistoryPage — G49 Phase 2.c.
 *
 * Renders, per student:
 *   1. A "current program" header card (latest active enrollment).
 *   2. An academic timeline grouped by academic year, with each enrollment
 *      row showing class, period, program, and status.
 *   3. A program-history event log, newest first, showing every program
 *      change (from → to, reason, actor, timestamp).
 *
 * Backend authorization (program_service._authorize_student_read) decides
 * which students each role can see. The frontend just wires the route to
 * all logged-in roles and surfaces 404s as a friendly empty state.
 */

import { useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { formatDate } from '@/shared/i18n';
import { EmptyState, ErrorBanner, LoadingState, toBannerError } from '@/shared/ui';
import {
  useStudentAcademicTimelineQuery,
  useStudentCurrentProgramQuery,
  useStudentTranscriptHtmlMutation,
  useStudentTranscriptPdfMutation,
  useStudentProgramHistoryQuery,
  useSnapshotTranscriptHtmlMutation,
  useSnapshotTranscriptPdfMutation,
  useSnapshotTranscriptMutation,
  useStudentSnapshotsQuery,
  useTakeSnapshotMutation,
} from './usePrograms';
import { EligibilityCheckTile } from './EligibilityCheckTile';
import type {
  AcademicTimelineEntry,
  ProgramAssignmentEvent,
  ProgramAssignmentReason,
} from './programs.service';

/** Group timeline entries by academic year, preserving server order
 *  (oldest year first; oldest period first within each year). */
function groupByYear(items: AcademicTimelineEntry[]) {
  const map = new Map<
    string,
    { label: string | null; date_start: string; entries: AcademicTimelineEntry[] }
  >();
  for (const entry of items) {
    const existing = map.get(entry.academic_year_id);
    if (existing) {
      existing.entries.push(entry);
    } else {
      map.set(entry.academic_year_id, {
        label: entry.academic_year_label,
        date_start: entry.academic_year_start,
        entries: [entry],
      });
    }
  }
  return Array.from(map.entries()).map(([id, payload]) => ({
    id,
    ...payload,
  }));
}

function reasonI18nKey(reason: ProgramAssignmentReason) {
  return `admin.programs.assign.reason.${reason}`;
}

function downloadJson(payload: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: 'application/json;charset=utf-8',
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function openBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.target = '_blank';
  link.rel = 'noopener noreferrer';
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

interface TranscriptPreviewState {
  title: string;
  html: string;
}

export function StudentAcademicHistoryPage() {
  const { t, i18n } = useTranslation();
  const { studentId = '' } = useParams<{ studentId: string }>();

  const currentQuery = useStudentCurrentProgramQuery(studentId);
  const timelineQuery = useStudentAcademicTimelineQuery(studentId);
  const historyQuery = useStudentProgramHistoryQuery(studentId);

  const groupedTimeline = useMemo(
    () => groupByYear(timelineQuery.data ?? []),
    [timelineQuery.data],
  );

  const dismissibleError = useDismissibleError(
    useMemo(
      () =>
        toBannerError(
          currentQuery.error ?? timelineQuery.error ?? historyQuery.error,
          t('app.error'),
        ),
      [currentQuery.error, historyQuery.error, t, timelineQuery.error],
    ),
  );

  if (currentQuery.isLoading || timelineQuery.isLoading || historyQuery.isLoading) {
    return <LoadingState />;
  }

  const current = currentQuery.data;
  const timeline = timelineQuery.data ?? [];
  const history = historyQuery.data ?? [];

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{t('student.academicHistory.title')}</h1>
        <p className="page-subtitle">{t('student.academicHistory.subtitle')}</p>
      </div>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => {
          void currentQuery.refetch();
          void timelineQuery.refetch();
          void historyQuery.refetch();
        }}
      />

      {/* ---------------------------------------------------------------
       * Current program card
       * --------------------------------------------------------------- */}
      <section className="card" style={{ padding: 16, marginBottom: 24 }}>
        <h2 style={{ marginTop: 0 }}>{t('student.academicHistory.currentTitle')}</h2>
        {current && current.program ? (
          <div>
            <div style={{ fontSize: 18, fontWeight: 600 }}>
              <code>{current.program.code}</code> — {current.program.name}
            </div>
            <small style={{ color: 'var(--color-text-secondary)' }}>
              v{current.program.version_label}
            </small>
          </div>
        ) : (
          <span style={{ color: 'var(--color-text-secondary)' }}>
            {t('student.academicHistory.currentEmpty')}
          </span>
        )}
      </section>

      {/* ---------------------------------------------------------------
       * Academic timeline (year-grouped)
       * --------------------------------------------------------------- */}
      <section style={{ marginBottom: 32 }}>
        <h2>{t('student.academicHistory.timelineTitle')}</h2>
        {timeline.length === 0 ? (
          <EmptyState message={t('student.academicHistory.timelineEmpty')} icon="🗓️" />
        ) : (
          <div className="card" style={{ padding: 16 }}>
            {groupedTimeline.map((year) => (
              <div key={year.id} style={{ marginBottom: 24 }}>
                <h3 style={{ marginBottom: 8 }}>
                  {year.label || formatDate(year.date_start, i18n.language)}
                </h3>
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>{t('student.academicHistory.period')}</th>
                        <th>{t('student.academicHistory.class')}</th>
                        <th>{t('student.academicHistory.program')}</th>
                        <th>{t('student.academicHistory.status')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {year.entries.map((entry) => (
                        <tr key={entry.enrollment_id}>
                          <td>
                            {entry.period_label || `${entry.period_start} → ${entry.period_end}`}
                          </td>
                          <td>
                            <code>{entry.class_code}</code>
                            <div>{entry.class_name}</div>
                          </td>
                          <td>
                            {entry.program ? (
                              <span>
                                <code>{entry.program.code}</code> — {entry.program.name}{' '}
                                <small
                                  style={{
                                    color: 'var(--color-text-secondary)',
                                  }}
                                >
                                  v{entry.program.version_label}
                                </small>
                              </span>
                            ) : (
                              <span
                                style={{
                                  color: 'var(--color-text-secondary)',
                                }}
                              >
                                —
                              </span>
                            )}
                          </td>
                          <td>
                            <span
                              className="status-badge"
                              style={{
                                color:
                                  entry.status === 'active'
                                    ? 'var(--color-success)'
                                    : 'var(--color-text-secondary)',
                                borderColor:
                                  entry.status === 'active'
                                    ? 'var(--color-success)'
                                    : 'var(--color-text-secondary)',
                              }}
                            >
                              {t(
                                `admin.enrollments.status${entry.status.charAt(0).toUpperCase() + entry.status.slice(1)}`,
                                entry.status,
                              )}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ---------------------------------------------------------------
       * Program history (event log, newest first)
       * --------------------------------------------------------------- */}
      <section>
        <h2>{t('student.academicHistory.historyTitle')}</h2>
        {history.length === 0 ? (
          <EmptyState message={t('student.academicHistory.historyEmpty')} icon="📜" />
        ) : (
          <ol
            style={{
              listStyle: 'none',
              padding: 0,
              margin: 0,
              display: 'grid',
              gap: 12,
            }}
          >
            {history.map((event: ProgramAssignmentEvent) => (
              <li
                key={event.id}
                className="card"
                style={{ padding: 12 }}
                aria-label={t(reasonI18nKey(event.reason_code))}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <strong>{t(reasonI18nKey(event.reason_code))}</strong>
                  <span style={{ color: 'var(--color-text-secondary)' }}>
                    {formatDate(event.occurred_at, i18n.language)}
                  </span>
                </div>
                <div style={{ marginTop: 4 }}>
                  {event.from_program_id ? (
                    <span>
                      {t('student.academicHistory.from')}{' '}
                      <code>{event.from_program_id.slice(0, 8)}…</code>
                    </span>
                  ) : (
                    <span style={{ color: 'var(--color-text-secondary)' }}>
                      {t('student.academicHistory.fromInitial')}
                    </span>
                  )}
                  <span style={{ margin: '0 4px' }}>→</span>
                  <span>
                    {t('student.academicHistory.to')}{' '}
                    <code>{event.to_program_id.slice(0, 8)}…</code>
                  </span>
                </div>
                {event.reason_note && (
                  <p
                    style={{
                      marginTop: 6,
                      color: 'var(--color-text-secondary)',
                    }}
                  >
                    “{event.reason_note}”
                  </p>
                )}
              </li>
            ))}
          </ol>
        )}
      </section>

      {/* ---------------------------------------------------------------
       * Academic snapshots (Phase 3.3)
       * --------------------------------------------------------------- */}
      <SnapshotsSection studentId={studentId} />

      {/* ---------------------------------------------------------------
       * Eligibility check (Phase 3.4)
       * --------------------------------------------------------------- */}
      <EligibilityCheckTile studentId={studentId} />
    </div>
  );
}

/**
 * Embedded "academic snapshots" section. Lists existing snapshots and lets
 * an admin take a new one — but ONLY when the student has at least one
 * enrollment (we use the timeline to surface a valid academic_year_id).
 */
function SnapshotsSection({ studentId }: { studentId: string }) {
  const { t } = useTranslation();
  const snapshotsQuery = useStudentSnapshotsQuery(studentId);
  const timelineQuery = useStudentAcademicTimelineQuery(studentId);
  const takeMutation = useTakeSnapshotMutation();
  const transcriptMutation = useSnapshotTranscriptMutation();
  const transcriptHtmlMutation = useSnapshotTranscriptHtmlMutation();
  const liveTranscriptHtmlMutation = useStudentTranscriptHtmlMutation();
  const transcriptPdfMutation = useSnapshotTranscriptPdfMutation();
  const liveTranscriptPdfMutation = useStudentTranscriptPdfMutation();
  const [preview, setPreview] = useState<TranscriptPreviewState | null>(null);

  // Admins typically take a snapshot for the most recent academic year on
  // the timeline. We expose that as the default; for explicit per-year
  // snapshots admins can use POST /academic-snapshots directly.
  const latestYear = useMemo(() => {
    const items = timelineQuery.data ?? [];
    if (items.length === 0) return null;
    return items[items.length - 1];
  }, [timelineQuery.data]);

  async function handleTake() {
    if (!latestYear) return;
    await takeMutation.mutateAsync({
      student_id: studentId,
      academic_year_id: latestYear.academic_year_id,
      snapshot_kind: 'MANUAL',
    });
  }

  async function handleDownloadTranscript(snapshotId: string) {
    const transcript = await transcriptMutation.mutateAsync(snapshotId);
    downloadJson(transcript, `transcript-${studentId}-${snapshotId}.json`);
  }

  async function handlePreviewLiveTranscript() {
    if (!latestYear) return;
    const html = await liveTranscriptHtmlMutation.mutateAsync({
      studentId,
      academicYearId: latestYear.academic_year_id,
      mode: 'preview',
    });
    setPreview({
      title: t('student.academicHistory.transcriptPreviewLive', {
        defaultValue: 'Live transcript preview',
      }),
      html,
    });
  }

  async function handlePreviewSnapshotTranscript(snapshotId: string) {
    const html = await transcriptHtmlMutation.mutateAsync(snapshotId);
    setPreview({
      title: t('student.academicHistory.transcriptPreviewSnapshot', {
        defaultValue: 'Snapshot transcript preview',
      }),
      html,
    });
  }

  async function handleDownloadLiveTranscriptPdf() {
    if (!latestYear) return;
    const blob = await liveTranscriptPdfMutation.mutateAsync({
      studentId,
      academicYearId: latestYear.academic_year_id,
      mode: 'preview',
    });
    openBlob(blob, `transcript-${studentId}-${latestYear.academic_year_id}.pdf`);
  }

  async function handleDownloadSnapshotTranscriptPdf(snapshotId: string) {
    const blob = await transcriptPdfMutation.mutateAsync(snapshotId);
    openBlob(blob, `transcript-${studentId}-${snapshotId}.pdf`);
  }

  return (
    <section style={{ marginTop: 32 }}>
      <h2>
        {t('student.academicHistory.snapshotsTitle', {
          defaultValue: 'Academic snapshots',
        })}
      </h2>
      {latestYear && (
        <div style={{ display: 'flex', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => void handleTake()}
            disabled={takeMutation.isPending}
          >
            {takeMutation.isPending
              ? t('app.loading')
              : t('student.academicHistory.takeSnapshot', {
                  defaultValue: 'Take a snapshot now',
                })}
          </button>
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={() => void handlePreviewLiveTranscript()}
            disabled={liveTranscriptHtmlMutation.isPending}
          >
            {liveTranscriptHtmlMutation.isPending
              ? t('app.loading')
              : t('student.academicHistory.transcriptPreviewLive', {
                  defaultValue: 'Live transcript preview',
                })}
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => void handleDownloadLiveTranscriptPdf()}
            disabled={liveTranscriptPdfMutation.isPending}
          >
            {liveTranscriptPdfMutation.isPending
              ? t('app.loading')
              : t('student.academicHistory.transcriptDownloadPdf', {
                  defaultValue: 'Open transcript PDF',
                })}
          </button>
        </div>
      )}
      {(snapshotsQuery.data?.length ?? 0) === 0 ? (
        <EmptyState
          message={t('student.academicHistory.snapshotsEmpty', {
            defaultValue: 'No snapshots taken yet.',
          })}
          icon="❄️"
        />
      ) : (
        <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: 8 }}>
          {(snapshotsQuery.data ?? []).map((snapshot) => (
            <li key={snapshot.id} className="card" style={{ padding: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <strong>{snapshot.snapshot_kind}</strong>
                <span style={{ color: 'var(--color-text-secondary)' }}>
                  {snapshot.taken_at.split('T')[0]}
                </span>
              </div>
              <small style={{ color: 'var(--color-text-secondary)' }}>
                {t('student.academicHistory.snapshotYear', {
                  defaultValue: 'Year',
                })}
                : <code>{snapshot.academic_year_id.slice(0, 8)}…</code>
              </small>
              <div style={{ marginTop: 8 }}>
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={() => void handlePreviewSnapshotTranscript(snapshot.id)}
                  disabled={transcriptHtmlMutation.isPending}
                  style={{ marginRight: 8 }}
                >
                  {transcriptHtmlMutation.isPending
                    ? t('app.loading')
                    : t('student.academicHistory.transcriptPreviewSnapshot', {
                        defaultValue: 'Snapshot transcript preview',
                      })}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => void handleDownloadSnapshotTranscriptPdf(snapshot.id)}
                  disabled={transcriptPdfMutation.isPending}
                  style={{ marginRight: 8 }}
                >
                  {transcriptPdfMutation.isPending
                    ? t('app.loading')
                    : t('student.academicHistory.transcriptDownloadPdf', {
                        defaultValue: 'Open transcript PDF',
                      })}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => void handleDownloadTranscript(snapshot.id)}
                  disabled={transcriptMutation.isPending}
                >
                  {transcriptMutation.isPending
                    ? t('app.loading')
                    : t('student.academicHistory.transcriptDownload', {
                        defaultValue: 'Download transcript JSON',
                      })}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
      {preview && (
        <TranscriptPreviewModal
          title={preview.title}
          html={preview.html}
          onClose={() => setPreview(null)}
        />
      )}
    </section>
  );
}

function TranscriptPreviewModal({
  title,
  html,
  onClose,
}: {
  title: string;
  html: string;
  onClose: () => void;
}) {
  const iframeRef = useRef<HTMLIFrameElement | null>(null);

  function handlePrint() {
    const frame = iframeRef.current;
    const frameWindow = frame?.contentWindow;
    if (!frameWindow) return;
    frameWindow.focus();
    frameWindow.print();
  }

  return (
    <div className="modal-overlay" onClick={onClose} role="presentation">
      <div
        className="modal-card"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        style={{ maxWidth: 1100, width: '95vw', padding: 16 }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 12,
            gap: 12,
          }}
        >
          <strong>{title}</strong>
          <div style={{ display: 'flex', gap: 8 }}>
            <button type="button" className="btn btn-primary btn-sm" onClick={handlePrint}>
              Print
            </button>
            <button type="button" className="btn btn-secondary btn-sm" onClick={onClose}>
              Close
            </button>
          </div>
        </div>
        <iframe
          ref={iframeRef}
          title={title}
          srcDoc={html}
          style={{
            width: '100%',
            minHeight: '75vh',
            border: '1px solid var(--color-border)',
            background: '#fff',
          }}
        />
      </div>
    </div>
  );
}
