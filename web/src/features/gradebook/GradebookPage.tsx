import { useEffect, useMemo, useState } from 'react';
import { FormProvider, useForm, type Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import { useTeacherClasses, useTeacherPeriods } from '@/features/teacher/useTeacher';
import { formatDate } from '@/shared/i18n';
import { ErrorBanner, Skeleton, StatCard } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import { gradebookService } from './gradebook.service';
import type { GradebookGrid, GradebookWeightedSummary } from './gradebook.types';
import { useClassGradebook, useUpdateGrades, useWeightedSummary } from './useGradebook';

type GradebookFormValues = {
  grades: Record<string, Record<string, number | null>>;
};

const gradeCellSchema = z.preprocess((value) => {
  if (value === '' || value === null || value === undefined) {
    return null;
  }

  if (typeof value === 'number') {
    return value;
  }

  if (typeof value === 'string') {
    const parsed = Number(value);
    return Number.isNaN(parsed) ? value : parsed;
  }

  return value;
}, z.number().min(0).max(20).multipleOf(0.5).nullable());

function createGradebookSchema(grid: GradebookGrid | undefined) {
  if (!grid) {
    return z.object({
      grades: z.record(z.string(), z.record(z.string(), gradeCellSchema)),
    });
  }

  return z.object({
    grades: z.object(
      Object.fromEntries(
        grid.entries.map((entry) => [
          entry.student_id,
          z.object(
            Object.fromEntries(
              grid.columns.map((column) => [column.assessment_id, gradeCellSchema])
            )
          ),
        ])
      )
    ),
  });
}

function buildDefaultValues(grid: GradebookGrid | undefined): GradebookFormValues {
  return {
    grades: Object.fromEntries(
      (grid?.entries ?? []).map((entry) => [
        entry.student_id,
        Object.fromEntries(
          (grid?.columns ?? []).map((column) => [
            column.assessment_id,
            entry.grades[column.assessment_id] ?? null,
          ])
        ),
      ])
    ),
  };
}

function getNumericValue(value: number | null | undefined) {
  return value === null || value === undefined || Number.isNaN(value) ? null : value;
}

function computeWeightedAverage(
  studentId: string,
  columns: GradebookGrid['columns'],
  gradeValues: GradebookFormValues['grades']
) {
  const totals = columns.reduce(
    (accumulator, column) => {
      const value = getNumericValue(gradeValues?.[studentId]?.[column.assessment_id]);
      if (value === null) {
        return accumulator;
      }

      accumulator.weightedSum += value * column.weight;
      accumulator.totalWeight += column.weight;
      return accumulator;
    },
    { weightedSum: 0, totalWeight: 0 }
  );

  if (totals.totalWeight === 0) {
    return 0;
  }

  return totals.weightedSum / totals.totalWeight;
}

function buildFallbackSummary(grid: GradebookGrid | undefined): GradebookWeightedSummary {
  const averages = (grid?.entries ?? []).map((entry) => entry.weighted_average);
  const classAverage =
    averages.length === 0
      ? 0
      : averages.reduce((sum, value) => sum + value, 0) / averages.length;

  return {
    class_id: grid?.class_id ?? '',
    class_average: classAverage,
    pass_rate:
      averages.length === 0
        ? 0
        : Math.round((averages.filter((value) => value >= 10).length / averages.length) * 100),
    highest_average: averages.length === 0 ? 0 : Math.max(...averages),
    lowest_average: averages.length === 0 ? 0 : Math.min(...averages),
  };
}

export function GradebookPage() {
  const { t, i18n } = useTranslation();
  const [selectedClassId, setSelectedClassId] = useState('');
  const [selectedPeriodId, setSelectedPeriodId] = useState('');
  const [exportFormat, setExportFormat] = useState<'csv' | 'pdf'>('csv');
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [exportMessage, setExportMessage] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  const classesQuery = useTeacherClasses();
  const periodsQuery = useTeacherPeriods();
  const gradebookQuery = useClassGradebook(selectedClassId);
  const weightedSummaryQuery = useWeightedSummary(selectedClassId);
  const updateGradesMutation = useUpdateGrades();
  const gradebookSchema = useMemo(
    () => createGradebookSchema(gradebookQuery.data),
    [gradebookQuery.data]
  );

  const methods = useForm<GradebookFormValues>({
    resolver: zodResolver(gradebookSchema) as Resolver<GradebookFormValues>,
    defaultValues: {
      grades: {},
    },
    mode: 'onBlur',
  });

  const watchedGrades = methods.watch('grades');
  const bannerError = useMemo(
    () =>
      toBannerError(
        classesQuery.error ??
          periodsQuery.error ??
          gradebookQuery.error ??
          weightedSummaryQuery.error ??
          updateGradesMutation.error ??
          exportError,
        t('app.error')
      ),
    [
      classesQuery.error,
      exportError,
      gradebookQuery.error,
      periodsQuery.error,
      t,
      updateGradesMutation.error,
      weightedSummaryQuery.error,
    ]
  );

  useEffect(() => {
    if (!selectedClassId && (classesQuery.data?.length ?? 0) > 0) {
      setSelectedClassId(classesQuery.data?.[0].id ?? '');
    }
  }, [classesQuery.data, selectedClassId]);

  useEffect(() => {
    if (!selectedPeriodId && (periodsQuery.data?.length ?? 0) > 0) {
      setSelectedPeriodId(periodsQuery.data?.[0].id ?? '');
    }
  }, [periodsQuery.data, selectedPeriodId]);

  useEffect(() => {
    methods.reset(buildDefaultValues(gradebookQuery.data));
  }, [gradebookQuery.data, methods]);

  const summary = weightedSummaryQuery.data ?? buildFallbackSummary(gradebookQuery.data);

  async function handleExport() {
    if (!selectedClassId) {
      return;
    }

    setExportError(null);
    setExportMessage(null);
    setIsExporting(true);

    try {
      const response = await gradebookService.exportGrades(selectedClassId, exportFormat);
      if (response.data.download_url) {
        window.open(response.data.download_url, '_blank', 'noopener,noreferrer');
      }
      setExportMessage(t('gradebook.exportReady', { format: exportFormat.toUpperCase() }));
    } catch (error) {
      setExportError(error instanceof Error ? error.message : t('gradebook.exportFailed'));
    } finally {
      setIsExporting(false);
    }
  }

  async function handleSubmit(values: GradebookFormValues) {
    if (!selectedClassId || !gradebookQuery.data) {
      return;
    }

    const payload = {
      class_id: selectedClassId,
      grades: gradebookQuery.data.entries.flatMap((entry) =>
        gradebookQuery.data.columns.flatMap((column) => {
          const value = getNumericValue(values.grades[entry.student_id]?.[column.assessment_id]);
          if (value === null) {
            return [];
          }
          return [
            {
              student_id: entry.student_id,
              assessment_id: column.assessment_id,
              value,
            },
          ];
        })
      ),
    };

    await updateGradesMutation.mutateAsync(payload);
    setSuccessMessage(t('gradebook.saved'));
  }

  return (
    <div className="page gradebook-page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('gradebook.title')}</h1>
          <p className="page-subtitle">{gradebookQuery.data?.class_name ?? t('gradebook.subtitle')}</p>
        </div>
        <div className="gradebook-page__toolbar">
          <label className="attendance-filter">
            <span className="attendance-filter__label">{t('gradebook.class')}</span>
            <select
              className="filter-select"
              value={selectedClassId}
              onChange={(event) => setSelectedClassId(event.target.value)}
            >
              {(classesQuery.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.code} · {item.name}
                </option>
              ))}
            </select>
          </label>

          <label className="attendance-filter">
            <span className="attendance-filter__label">{t('gradebook.period')}</span>
            <select
              className="filter-select"
              value={selectedPeriodId}
              onChange={(event) => setSelectedPeriodId(event.target.value)}
            >
              {(periodsQuery.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label || `${formatDate(item.date_start, i18n.language)} → ${formatDate(item.date_end, i18n.language)}`}
                </option>
              ))}
            </select>
          </label>

          <label className="attendance-filter">
            <span className="attendance-filter__label">{t('gradebook.export')}</span>
            <select
              className="filter-select"
              value={exportFormat}
              onChange={(event) => setExportFormat(event.target.value as 'csv' | 'pdf')}
            >
              <option value="csv">CSV</option>
              <option value="pdf">PDF</option>
            </select>
          </label>

          <div className="gradebook-page__actions">
            <button
              type="button"
              className="btn btn-secondary"
              disabled={isExporting || !selectedClassId}
              onClick={() => void handleExport()}
            >
              {isExporting ? t('app.loading') : t('gradebook.export')}
            </button>
          </div>
        </div>
      </div>

      <ErrorBanner error={bannerError} />

      {successMessage && <div className="attendance-banner attendance-banner--success">{successMessage}</div>}
      {exportMessage && <div className="attendance-banner attendance-banner--success">{exportMessage}</div>}

      {classesQuery.isLoading || periodsQuery.isLoading || gradebookQuery.isLoading ? (
        <div className="gradebook-page__loading">
          <Skeleton variant="card" count={3} />
          <Skeleton variant="table-row" count={6} />
        </div>
      ) : (
        <>
          <div className="gradebook-page__stats">
            <StatCard label="gradebook.classAverage" value={summary.class_average.toFixed(2)} />
            <StatCard label="gradebook.passRate" value={`${summary.pass_rate}%`} />
            <StatCard label="gradebook.highestAverage" value={summary.highest_average.toFixed(2)} />
            <StatCard label="gradebook.lowestAverage" value={summary.lowest_average.toFixed(2)} />
          </div>

          <FormProvider {...methods}>
            <form onSubmit={methods.handleSubmit(handleSubmit)} className="gradebook-page__form">
              <div className="gradebook-table-shell">
                <table className="gradebook-table">
                  <thead>
                    <tr>
                      <th>{t('gradebook.student')}</th>
                      {(gradebookQuery.data?.columns ?? []).map((column) => (
                        <th key={column.assessment_id}>
                          <div className="gradebook-table__header">
                            <strong>{column.title}</strong>
                            <span>{Math.round(column.weight * 100)}%</span>
                          </div>
                        </th>
                      ))}
                      <th>{t('gradebook.weightedAverage')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(gradebookQuery.data?.entries ?? []).map((entry) => {
                      const weightedAverage = computeWeightedAverage(
                        entry.student_id,
                        gradebookQuery.data?.columns ?? [],
                        watchedGrades ?? {}
                      );

                      return (
                        <tr key={entry.student_id}>
                          <td className="gradebook-table__student">
                            <strong>{entry.student_name}</strong>
                          </td>
                          {(gradebookQuery.data?.columns ?? []).map((column) => {
                            const fieldName =
                              `grades.${entry.student_id}.${column.assessment_id}` as const;
                            const cellValue = getNumericValue(
                              watchedGrades?.[entry.student_id]?.[column.assessment_id]
                            );
                            const isPass = cellValue !== null && cellValue >= 10;

                            return (
                              <td key={column.assessment_id}>
                                <input
                                  type="number"
                                  step="0.5"
                                  min="0"
                                  max="20"
                                  className={`gradebook-cell ${
                                    cellValue === null
                                      ? ''
                                      : isPass
                                        ? 'gradebook-cell--pass'
                                        : 'gradebook-cell--fail'
                                  }`}
                                  {...methods.register(fieldName, { valueAsNumber: true })}
                                />
                              </td>
                            );
                          })}
                          <td>
                            <span
                              className={`gradebook-average ${
                                weightedAverage >= 10
                                  ? 'gradebook-average--pass'
                                  : 'gradebook-average--fail'
                              }`}
                            >
                              {weightedAverage.toFixed(2)}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <div className="gradebook-page__footer">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={updateGradesMutation.isPending || !selectedClassId}
                >
                  {updateGradesMutation.isPending ? t('app.loading') : t('gradebook.saveAll')}
                </button>
              </div>
            </form>
          </FormProvider>
        </>
      )}
    </div>
  );
}
