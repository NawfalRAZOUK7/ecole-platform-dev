/**
 * MyChildrenPage — Parent-facing overview of linked children with quick actions.
 *
 * Phase I (Web/Mobile parity) — I5.
 *
 * Mirrors mobile `my_children_screen.dart`. Fetches GET /progress/children
 * (via useChildrenProgressOverview), renders a responsive card grid with
 * avatar, name, headline metrics, and quick-action buttons that navigate
 * to the existing detail pages using ?studentId= query param.
 */

import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { useChildrenProgressOverview } from '@/features/progress/useProgress';
import type { ChildSummary } from '@/features/progress/progress.service';

function gradeColor(value: number): string {
  if (value >= 80) return 'var(--color-success)';
  if (value >= 50) return 'var(--color-warning)';
  return 'var(--color-error)';
}

interface ChildCardProps {
  child: ChildSummary;
  onNavigate: (path: string) => void;
  t: ReturnType<typeof useTranslation>['t'];
}

function ChildCard({ child, onNavigate, t }: ChildCardProps) {
  const initials = child.student_name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join('');

  return (
    <div className="child-progress-card" data-testid={`child-card-${child.student_id}`}>
      <div className="child-card-header">
        <div className="child-avatar" aria-hidden="true">
          {initials || '?'}
        </div>
        <h3 className="child-name">{child.student_name}</h3>
      </div>

      <div className="child-metrics">
        <div className="child-metric">
          <span className="metric-label">{t('progress.gradeAvg')}</span>
          <span className="metric-value" style={{ color: gradeColor(child.grade_average) }}>
            {child.grade_average.toFixed(1)}
          </span>
        </div>
        <div className="child-metric">
          <span className="metric-label">{t('progress.attendanceRate')}</span>
          <span className="metric-value">{child.attendance_rate.toFixed(0)}%</span>
        </div>
        <div className="child-metric">
          <span className="metric-label">{t('progress.contentRate')}</span>
          <span className="metric-value">{child.content_completion_rate.toFixed(0)}%</span>
        </div>
      </div>

      {child.latest_grade && (
        <div className="child-latest">
          {t('progress.latestGrade')}: <strong>{child.latest_grade.score}</strong> —{' '}
          {child.latest_grade.assignment}
        </div>
      )}

      <div className="child-card-actions">
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => onNavigate(`/progress?studentId=${child.student_id}`)}
        >
          {t('family.actions.viewProgress')}
        </button>
        <button
          type="button"
          className="btn"
          onClick={() => onNavigate(`/results?studentId=${child.student_id}`)}
        >
          {t('family.actions.viewGrades')}
        </button>
        <button
          type="button"
          className="btn"
          onClick={() => onNavigate(`/timetable?studentId=${child.student_id}`)}
        >
          {t('family.actions.viewTimetable')}
        </button>
        <button
          type="button"
          className="btn"
          onClick={() => onNavigate(`/family/review/${child.student_id}`)}
        >
          {t('family.actions.reviewSessions', 'Review sessions')}
        </button>
      </div>
    </div>
  );
}

export function MyChildrenPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const childrenQuery = useChildrenProgressOverview();

  if (childrenQuery.isLoading) {
    return <LoadingState />;
  }

  if (childrenQuery.error) {
    return (
      <ErrorBanner
        error={childrenQuery.error instanceof Error ? childrenQuery.error.message : t('app.error')}
        onRetry={() => void childrenQuery.refetch()}
      />
    );
  }

  const data = childrenQuery.data;

  if (!data || data.children.length === 0) {
    return (
      <div className="parent-progress">
        <h1 className="page-title">{t('family.title')}</h1>
        <div className="empty-state">
          <p>{t('family.empty')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="parent-progress">
      <h1 className="page-title">{t('family.title')}</h1>
      <p className="page-subtitle">{t('family.subtitle', { count: data.child_count })}</p>

      <div className="child-progress-cards">
        {data.children.map((child) => (
          <ChildCard
            key={child.student_id}
            child={child}
            onNavigate={(path) => navigate(path)}
            t={t}
          />
        ))}
      </div>
    </div>
  );
}
