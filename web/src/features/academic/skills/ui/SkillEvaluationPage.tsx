import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/app/providers/AuthContext';
import { DataTable, ErrorBanner, LoadingState, StatCard } from '@/shared/ui';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { SkillDimension } from '../model/skills.types';
import { useEvaluateStudentSkills, useSkillDimensions } from '../model/useSkills';

type MetricRow = {
  metric: string;
  value: string;
} & Record<string, unknown>;

function getDimensionLabel(dimension: SkillDimension, language: string) {
  if (language.startsWith('ar')) {
    return dimension.name_ar;
  }
  if (language.startsWith('en')) {
    return dimension.name_en;
  }
  return dimension.name_fr;
}

export function SkillEvaluationPage() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const [studentId, setStudentId] = useState('');
  const [academicYearId, setAcademicYearId] = useState('');
  const [ratings, setRatings] = useState<Record<string, number>>({});
  const dimensionsQuery = useSkillDimensions();
  const evaluateMutation = useEvaluateStudentSkills();

  useEffect(() => {
    if (!studentId && user?.role === 'STD' && user.id) {
      setStudentId(user.id);
    }
  }, [studentId, user]);

  useEffect(() => {
    if ((dimensionsQuery.data?.length ?? 0) === 0) {
      return;
    }

    setRatings((current) => {
      const next = { ...current };
      (dimensionsQuery.data ?? []).forEach((dimension) => {
        if (!next[dimension.id]) {
          next[dimension.id] = 3;
        }
      });
      return next;
    });
  }, [dimensionsQuery.data]);

  const metricColumns: ColumnDef<MetricRow>[] = useMemo(
    () => [
      { key: 'metric', header: 'skills.metric' },
      { key: 'value', header: 'skills.value' },
    ],
    [],
  );

  const metricRows = useMemo<MetricRow[]>(
    () =>
      Object.entries(evaluateMutation.data?.data.metrics ?? {}).map(([metric, value]) => ({
        metric,
        value: String(value),
      })),
    [evaluateMutation.data?.data.metrics],
  );

  async function handleEvaluate() {
    if (!studentId || !academicYearId) {
      return;
    }

    await evaluateMutation.mutateAsync({
      studentId,
      academicYearId,
    });
  }

  if (dimensionsQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{t('skills.evaluationTitle')}</h1>
        <p className="page-subtitle">{t('skills.evaluationSubtitle')}</p>
      </div>

      <ErrorBanner
        error={toBannerError(dimensionsQuery.error ?? evaluateMutation.error, t('app.error'))}
      />

      <div className="filters-bar">
        <input
          className="filter-input"
          value={studentId}
          onChange={(event) => setStudentId(event.target.value)}
          placeholder={t('skills.studentIdPlaceholder')}
        />
        <input
          className="filter-input"
          value={academicYearId}
          onChange={(event) => setAcademicYearId(event.target.value)}
          placeholder={t('skills.academicYearIdPlaceholder')}
        />
        <button
          type="button"
          className="btn btn-primary"
          disabled={!studentId || !academicYearId || evaluateMutation.isPending}
          onClick={() => void handleEvaluate()}
        >
          {evaluateMutation.isPending ? t('app.loading') : t('skills.runEvaluation')}
        </button>
      </div>

      <div className="card-list">
        {(dimensionsQuery.data ?? []).map((dimension) => (
          <div key={dimension.id} className="card">
            <div className="page-header page-header--split">
              <div>
                <h2>{getDimensionLabel(dimension, i18n.language)}</h2>
                <p>{dimension.description_fr || t('skills.noDescription')}</p>
              </div>
              <strong>{ratings[dimension.id] ?? 3}/5</strong>
            </div>
            <input
              type="range"
              min="1"
              max="5"
              step="1"
              value={ratings[dimension.id] ?? 3}
              onChange={(event) =>
                setRatings((current) => ({
                  ...current,
                  [dimension.id]: Number(event.target.value),
                }))
              }
              style={{ width: '100%' }}
              aria-label={getDimensionLabel(dimension, i18n.language)}
            />
          </div>
        ))}
      </div>

      {evaluateMutation.data?.data ? (
        <div className="card">
          <div className="stats-grid">
            <StatCard
              label="skills.overallScore"
              value={`${evaluateMutation.data?.data?.overall_score ?? 0}%`}
              icon="🏅"
            />
            <StatCard
              label="skills.unlocked"
              value={evaluateMutation.data?.data?.unlocked_milestones ?? 0}
              icon="✨"
            />
            <StatCard
              label="skills.totalMilestones"
              value={evaluateMutation.data?.data?.total_milestones ?? 0}
              icon="🏁"
            />
            <StatCard
              label="skills.progressEntries"
              value={evaluateMutation.data?.data?.progress_items?.length ?? 0}
              icon="📘"
            />
          </div>

          <DataTable
            columns={metricColumns}
            data={metricRows}
            loading={false}
            emptyMessage="skills.emptyMetrics"
            ariaLabel={t('skills.evaluationResults')}
          />
        </div>
      ) : null}
    </div>
  );
}
