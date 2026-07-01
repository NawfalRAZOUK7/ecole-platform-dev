import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { ColumnDef } from '@/shared/ui/DataTable';
import { DataTable, ErrorBanner, LoadingState, Tabs } from '@/shared/ui';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { CurriculumMapping } from '../model/compliance.types';
import {
  useCreateCurriculum,
  useCreateMapping,
  useCreateObjective,
  useCurricula,
  useCurriculumMappings,
  useCurriculumObjectives,
  useDeleteMapping,
} from '../model/useCompliance';

type MappingRow = CurriculumMapping & Record<string, unknown>;

export function CurriculumMappingPage() {
  const { t } = useTranslation();
  const [selectedCurriculumId, setSelectedCurriculumId] = useState('');
  const [selectedObjectiveId, setSelectedObjectiveId] = useState('');
  const [courseId, setCourseId] = useState('');
  const [contentItemId, setContentItemId] = useState('');
  const [coveragePercent, setCoveragePercent] = useState('100');
  const [notes, setNotes] = useState('');
  const [curriculumForm, setCurriculumForm] = useState({
    level: '',
    grade: '',
    subject: '',
    academic_year: '',
    version: '1.0',
  });
  const [objectiveForm, setObjectiveForm] = useState({
    code: '',
    title_fr: '',
    title_ar: '',
    description_fr: '',
    trimester: 1,
    unit_number: 1,
    hours_recommended: '1',
    display_order: '0',
  });

  const curriculaQuery = useCurricula();
  const objectivesQuery = useCurriculumObjectives(selectedCurriculumId);
  const mappingsQuery = useCurriculumMappings({
    curriculum_id: selectedCurriculumId || undefined,
  });
  const createCurriculumMutation = useCreateCurriculum();
  const createObjectiveMutation = useCreateObjective();
  const createMappingMutation = useCreateMapping();
  const deleteMappingMutation = useDeleteMapping();

  useEffect(() => {
    if (!selectedCurriculumId && (curriculaQuery.data?.length ?? 0) > 0) {
      setSelectedCurriculumId(curriculaQuery.data?.[0].id ?? '');
    }
  }, [curriculaQuery.data, selectedCurriculumId]);

  useEffect(() => {
    if (!selectedObjectiveId && (objectivesQuery.data?.length ?? 0) > 0) {
      setSelectedObjectiveId(objectivesQuery.data?.[0].id ?? '');
    }
  }, [objectivesQuery.data, selectedObjectiveId]);

  const mappingColumns: ColumnDef<MappingRow>[] = useMemo(
    () => [
      { key: 'objective_code', header: 'compliance.objectiveCode' },
      { key: 'course_id', header: 'compliance.courseId' },
      { key: 'content_item_id', header: 'compliance.contentItemId' },
      { key: 'coverage_percent', header: 'compliance.coveragePercent' },
      {
        key: 'id',
        header: 'compliance.actions',
        sortable: false,
        render: (_value, row) => (
          <button
            type="button"
            className="btn btn-danger btn-sm"
            onClick={() => void deleteMappingMutation.mutateAsync(row.id)}
          >
            {t('compliance.deleteMapping')}
          </button>
        ),
      },
    ],
    [deleteMappingMutation, t],
  );

  async function handleCreateCurriculum() {
    await createCurriculumMutation.mutateAsync({
      ...curriculumForm,
      is_active: true,
    });
  }

  async function handleCreateObjective() {
    if (!selectedCurriculumId) {
      return;
    }

    await createObjectiveMutation.mutateAsync({
      curriculumId: selectedCurriculumId,
      payload: {
        ...objectiveForm,
        is_mandatory: true,
        hours_recommended: Number(objectiveForm.hours_recommended),
        display_order: Number(objectiveForm.display_order),
      },
    });
  }

  async function handleCreateMapping() {
    if (!selectedObjectiveId) {
      return;
    }

    await createMappingMutation.mutateAsync({
      objective_id: selectedObjectiveId,
      course_id: courseId || null,
      content_item_id: contentItemId || null,
      coverage_percent: Number(coveragePercent),
      notes: notes || null,
    });
  }

  if (curriculaQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{t('compliance.mappingTitle')}</h1>
        <p className="page-subtitle">{t('compliance.mappingSubtitle')}</p>
      </div>

      <ErrorBanner
        error={toBannerError(
          curriculaQuery.error ??
            objectivesQuery.error ??
            mappingsQuery.error ??
            createCurriculumMutation.error ??
            createObjectiveMutation.error ??
            createMappingMutation.error ??
            deleteMappingMutation.error,
          t('app.error'),
        )}
      />

      <Tabs
        defaultTab="mapping"
        tabs={[
          {
            id: 'mapping',
            label: 'compliance.mappingTab',
            content: (
              <div className="card-list">
                <div className="card">
                  <h2>{t('compliance.selectionUi')}</h2>
                  <div className="filters-bar">
                    <select
                      className="filter-select"
                      aria-label={t('compliance.curriculumTab')}
                      value={selectedCurriculumId}
                      onChange={(event) => setSelectedCurriculumId(event.target.value)}
                    >
                      {(curriculaQuery.data ?? []).map((curriculum) => (
                        <option key={curriculum.id} value={curriculum.id}>
                          {curriculum.subject} · {curriculum.grade}
                        </option>
                      ))}
                    </select>
                    <select
                      className="filter-select"
                      aria-label={t('compliance.objectiveTab')}
                      value={selectedObjectiveId}
                      onChange={(event) => setSelectedObjectiveId(event.target.value)}
                    >
                      {(objectivesQuery.data ?? []).map((objective) => (
                        <option key={objective.id} value={objective.id}>
                          {objective.code} · {objective.title_fr}
                        </option>
                      ))}
                    </select>
                    <input
                      className="filter-input"
                      aria-label={t('compliance.courseId')}
                      value={courseId}
                      onChange={(event) => setCourseId(event.target.value)}
                      placeholder={t('compliance.courseId')}
                    />
                    <input
                      className="filter-input"
                      aria-label={t('compliance.contentItemId')}
                      value={contentItemId}
                      onChange={(event) => setContentItemId(event.target.value)}
                      placeholder={t('compliance.contentItemId')}
                    />
                    <input
                      className="filter-input"
                      aria-label={t('compliance.coveragePercent')}
                      type="number"
                      min="0"
                      max="100"
                      value={coveragePercent}
                      onChange={(event) => setCoveragePercent(event.target.value)}
                      placeholder={t('compliance.coveragePercent')}
                    />
                    <input
                      className="filter-input"
                      aria-label={t('compliance.notes')}
                      value={notes}
                      onChange={(event) => setNotes(event.target.value)}
                      placeholder={t('compliance.notes')}
                    />
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={() => void handleCreateMapping()}
                    >
                      {t('compliance.createMapping')}
                    </button>
                  </div>
                </div>
                <div className="card">
                  <DataTable
                    columns={mappingColumns}
                    data={(mappingsQuery.data ?? []) as MappingRow[]}
                    loading={mappingsQuery.isLoading}
                    emptyMessage="compliance.empty"
                    ariaLabel={t('compliance.mappingTitle')}
                  />
                </div>
              </div>
            ),
          },
          {
            id: 'curriculum',
            label: 'compliance.curriculumTab',
            content: (
              <div className="card">
                <div className="filters-bar">
                  <input
                    className="filter-input"
                    aria-label={t('compliance.level')}
                    value={curriculumForm.level}
                    onChange={(event) =>
                      setCurriculumForm({ ...curriculumForm, level: event.target.value })
                    }
                    placeholder={t('compliance.level')}
                  />
                  <input
                    className="filter-input"
                    aria-label={t('compliance.grade')}
                    value={curriculumForm.grade}
                    onChange={(event) =>
                      setCurriculumForm({ ...curriculumForm, grade: event.target.value })
                    }
                    placeholder={t('compliance.grade')}
                  />
                  <input
                    className="filter-input"
                    aria-label={t('compliance.subject')}
                    value={curriculumForm.subject}
                    onChange={(event) =>
                      setCurriculumForm({ ...curriculumForm, subject: event.target.value })
                    }
                    placeholder={t('compliance.subject')}
                  />
                  <input
                    className="filter-input"
                    aria-label={t('compliance.academicYear')}
                    value={curriculumForm.academic_year}
                    onChange={(event) =>
                      setCurriculumForm({ ...curriculumForm, academic_year: event.target.value })
                    }
                    placeholder={t('compliance.academicYear')}
                  />
                  <input
                    className="filter-input"
                    aria-label={t('compliance.version')}
                    value={curriculumForm.version}
                    onChange={(event) =>
                      setCurriculumForm({ ...curriculumForm, version: event.target.value })
                    }
                    placeholder={t('compliance.version')}
                  />
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => void handleCreateCurriculum()}
                  >
                    {t('compliance.createCurriculum')}
                  </button>
                </div>
              </div>
            ),
          },
          {
            id: 'objective',
            label: 'compliance.objectiveTab',
            content: (
              <div className="card">
                <div className="filters-bar">
                  <input
                    className="filter-input"
                    aria-label={t('compliance.objectiveCode')}
                    value={objectiveForm.code}
                    onChange={(event) =>
                      setObjectiveForm({ ...objectiveForm, code: event.target.value })
                    }
                    placeholder={t('compliance.objectiveCode')}
                  />
                  <input
                    className="filter-input"
                    aria-label={t('compliance.titleFr')}
                    value={objectiveForm.title_fr}
                    onChange={(event) =>
                      setObjectiveForm({ ...objectiveForm, title_fr: event.target.value })
                    }
                    placeholder={t('compliance.titleFr')}
                  />
                  <input
                    className="filter-input"
                    aria-label={t('compliance.titleAr')}
                    value={objectiveForm.title_ar}
                    onChange={(event) =>
                      setObjectiveForm({ ...objectiveForm, title_ar: event.target.value })
                    }
                    placeholder={t('compliance.titleAr')}
                  />
                  <input
                    className="filter-input"
                    aria-label={t('compliance.trimester')}
                    type="number"
                    min="1"
                    max="3"
                    value={objectiveForm.trimester}
                    onChange={(event) =>
                      setObjectiveForm({ ...objectiveForm, trimester: Number(event.target.value) })
                    }
                    placeholder={t('compliance.trimester')}
                  />
                  <input
                    className="filter-input"
                    aria-label={t('compliance.unitNumber')}
                    type="number"
                    min="1"
                    value={objectiveForm.unit_number}
                    onChange={(event) =>
                      setObjectiveForm({
                        ...objectiveForm,
                        unit_number: Number(event.target.value),
                      })
                    }
                    placeholder={t('compliance.unitNumber')}
                  />
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => void handleCreateObjective()}
                  >
                    {t('compliance.createObjective')}
                  </button>
                </div>
              </div>
            ),
          },
        ]}
      />
    </div>
  );
}
