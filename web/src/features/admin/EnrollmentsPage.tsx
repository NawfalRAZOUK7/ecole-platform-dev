/**
 * Admin Enrollments page — G49 Phase 2.b.
 *
 * Lists every enrollment in the school with student / class / period /
 * academic year / program embedded. Supports filtering by status and the
 * "needs program assignment" backlog (Phase 1 follow-up). Each row has an
 * "Assign program" affordance that opens the AssignProgramDialog.
 *
 * Calls:
 *   GET /admin/enrollments  (PERM-ERP:enrollment:read for ADM/DIR)
 */

import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState, ErrorBanner, LoadingState, toBannerError } from '@/shared/ui';
import { formatDate } from '@/shared/i18n';
import { AssignProgramDialog } from './AssignProgramDialog';
import { useAdminEnrollmentsQuery } from './useEnrollments';
import type { AdminEnrollmentRow } from './enrollments.service';

interface DialogState {
  enrollmentId: string;
  studentId: string;
  currentProgramId: string | null;
}

export function EnrollmentsPage() {
  const { t, i18n } = useTranslation();
  const [statusFilter, setStatusFilter] = useState('');
  const [missingProgramOnly, setMissingProgramOnly] = useState(false);
  const [dialog, setDialog] = useState<DialogState | null>(null);

  const filters = useMemo(
    () => ({
      status: statusFilter || undefined,
      missing_program: missingProgramOnly ? 1 : undefined,
    }),
    [statusFilter, missingProgramOnly],
  );
  const enrollmentsQuery = useAdminEnrollmentsQuery(filters);

  const items = useMemo<AdminEnrollmentRow[]>(
    () => enrollmentsQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [enrollmentsQuery.data],
  );

  const dismissibleError = useDismissibleError(
    useMemo(
      () => toBannerError(enrollmentsQuery.error, t('app.error')),
      [enrollmentsQuery.error, t],
    ),
  );

  if (enrollmentsQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('admin.enrollments.title')}</h1>
      <p className="page-subtitle">{t('admin.enrollments.subtitle')}</p>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void enrollmentsQuery.refetch()}
      />

      <div className="filters-bar">
        <select
          className="filter-select"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          aria-label={t('admin.enrollments.statusFilter')}
        >
          <option value="">{t('admin.enrollments.allStatuses')}</option>
          <option value="active">{t('admin.enrollments.statusActive')}</option>
          <option value="transferred">{t('admin.enrollments.statusTransferred')}</option>
          <option value="dropped">{t('admin.enrollments.statusDropped')}</option>
        </select>
        <label style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <input
            type="checkbox"
            checked={missingProgramOnly}
            onChange={(e) => setMissingProgramOnly(e.target.checked)}
          />
          {t('admin.enrollments.missingProgramOnly')}
        </label>
      </div>

      {items.length === 0 ? (
        <EmptyState message={t('admin.enrollments.empty')} icon="🎒" />
      ) : (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('admin.enrollments.student')}</th>
                  <th>{t('admin.enrollments.class')}</th>
                  <th>{t('admin.enrollments.period')}</th>
                  <th>{t('admin.enrollments.academicYear')}</th>
                  <th>{t('admin.enrollments.program')}</th>
                  <th>{t('admin.enrollments.status')}</th>
                  <th>{t('admin.enrollments.created')}</th>
                  <th>{t('admin.enrollments.actions')}</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <Link
                        to={`/students/${row.student.id}/academic-history`}
                        title={t('admin.enrollments.viewAcademicHistory')}
                      >
                        {row.student.full_name}
                      </Link>
                      <small
                        style={{
                          color: 'var(--color-text-secondary)',
                          display: 'block',
                        }}
                      >
                        {row.student.email}
                      </small>
                    </td>
                    <td>
                      <code>{row.class_.code}</code>
                      <div>{row.class_.name}</div>
                    </td>
                    <td>{row.period.label || row.period.id.slice(0, 8)}</td>
                    <td>{row.academic_year.label || '—'}</td>
                    <td>
                      {row.program ? (
                        <span>
                          <code>{row.program.code}</code> — {row.program.name}{' '}
                          <small style={{ color: 'var(--color-text-secondary)' }}>
                            v{row.program.version_label}
                          </small>
                        </span>
                      ) : (
                        <span
                          className="status-badge"
                          style={{
                            color: 'var(--color-warning)',
                            borderColor: 'var(--color-warning)',
                          }}
                        >
                          {t('admin.enrollments.noProgram')}
                        </span>
                      )}
                    </td>
                    <td>
                      <span
                        className="status-badge"
                        style={{
                          color:
                            row.status === 'active'
                              ? 'var(--color-success)'
                              : 'var(--color-text-secondary)',
                          borderColor:
                            row.status === 'active'
                              ? 'var(--color-success)'
                              : 'var(--color-text-secondary)',
                        }}
                      >
                        {t(
                          `admin.enrollments.status${row.status.charAt(0).toUpperCase() + row.status.slice(1)}`,
                          row.status,
                        )}
                      </span>
                    </td>
                    <td>{formatDate(row.created_at, i18n.language)}</td>
                    <td>
                      {row.status === 'active' && (
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() =>
                            setDialog({
                              enrollmentId: row.id,
                              studentId: row.student.id,
                              currentProgramId: row.program?.id ?? null,
                            })
                          }
                        >
                          {t('admin.enrollments.assignProgram')}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {enrollmentsQuery.hasNextPage && (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => void enrollmentsQuery.fetchNextPage()}
                disabled={enrollmentsQuery.isFetchingNextPage}
              >
                {enrollmentsQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          )}
        </>
      )}

      <AssignProgramDialog
        open={dialog !== null}
        enrollmentId={dialog?.enrollmentId ?? ''}
        studentId={dialog?.studentId}
        currentProgramId={dialog?.currentProgramId}
        onClose={() => setDialog(null)}
        onAssigned={() => {
          void enrollmentsQuery.refetch();
        }}
      />
    </div>
  );
}
