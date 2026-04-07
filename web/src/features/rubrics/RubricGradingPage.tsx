import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { useGradeRubric, useRubric, useRubricResults } from './useRubrics';
import type { RubricGradeEntry } from './rubrics.types';

export function RubricGradingPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  const rubricQuery = useRubric(id ?? '');
  const resultsQuery = useRubricResults(id ?? '');
  const gradeMutation = useGradeRubric();

  const [studentId, setStudentId] = useState('');
  // Map: criterionId -> levelId
  const [selections, setSelections] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [savedStudentId, setSavedStudentId] = useState<string | null>(null);

  const rubric = rubricQuery.data;
  const results = resultsQuery.data?.results ?? [];

  const entries = useMemo<RubricGradeEntry[]>(() => {
    if (!rubric) return [];
    return rubric.criteria.flatMap((c) => {
      const levelId = selections[c.id];
      if (!levelId) return [];
      const level = c.levels.find((l) => l.id === levelId);
      if (!level) return [];
      return [{
        student_id: studentId,
        criterion_id: c.id,
        level_id: levelId,
        score: level.score * c.weight,
      }];
    });
  }, [rubric, selections, studentId]);

  const totalScore = useMemo(() => entries.reduce((sum, e) => sum + e.score, 0), [entries]);
  const maxScore = useMemo(() => {
    if (!rubric) return 0;
    return rubric.criteria.reduce((sum, c) => {
      const maxLevel = Math.max(...c.levels.map((l) => l.score));
      return sum + maxLevel * c.weight;
    }, 0);
  }, [rubric]);

  const pct = maxScore > 0 ? Math.round((totalScore / maxScore) * 100) : 0;
  const allSelected = rubric ? rubric.criteria.every((c) => Boolean(selections[c.id])) : false;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!id || !studentId.trim()) return;
    setError(null);
    try {
      await gradeMutation.mutateAsync({ rubric_id: id, entries });
      setSavedStudentId(studentId);
      setSelections({});
      setStudentId('');
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    }
  }

  if (rubricQuery.isLoading) return <LoadingState />;

  if (!rubric) {
    return (
      <div className="page">
        <ErrorBanner error={rubricQuery.error instanceof Error ? rubricQuery.error.message : t('app.error')} />
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('rubrics.gradingTitle')}</h1>
          <p className="page-subtitle">{rubric.title}</p>
        </div>
        <button type="button" className="btn btn-secondary" onClick={() => navigate(`/rubrics/${id}/edit`)}>
          {t('rubrics.edit')}
        </button>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      {savedStudentId && (
        <div style={{ padding: '10px 16px', background: 'var(--color-success-bg, #f0fdf4)', border: '1px solid var(--color-success)', borderRadius: 8, marginBottom: 16, color: 'var(--color-success)', fontSize: 14 }}>
          {t('rubrics.gradeSaved', { studentId: savedStudentId })}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-field" style={{ maxWidth: 320, marginBottom: 20 }}>
          <label htmlFor="studentId">{t('rubrics.studentId')}</label>
          <input
            id="studentId"
            className="input"
            required
            value={studentId}
            onChange={(e) => { setStudentId(e.target.value); setSavedStudentId(null); }}
            placeholder={t('rubrics.studentIdPlaceholder')}
            disabled={gradeMutation.isPending}
          />
        </div>

        <div style={{ overflowX: 'auto', marginBottom: 20 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: 'var(--color-surface)' }}>
                <th style={TH}>{t('rubrics.criterion')}</th>
                <th style={{ ...TH, width: 52 }}>{t('rubrics.weight')}</th>
                {rubric.criteria[0]?.levels.map((l) => (
                  <th key={l.id} style={TH}>
                    <div style={{ fontWeight: 600 }}>{l.label}</div>
                    <div style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>{l.score} pts</div>
                  </th>
                ))}
                <th style={TH}>{t('rubrics.cols.score')}</th>
              </tr>
            </thead>
            <tbody>
              {rubric.criteria.map((c) => {
                const selectedLevelId = selections[c.id];
                const selectedLevel = c.levels.find((l) => l.id === selectedLevelId);
                const rowScore = selectedLevel ? selectedLevel.score * c.weight : 0;

                return (
                  <tr key={c.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                    <td style={TD}>
                      <div style={{ fontWeight: 600 }}>{c.name}</div>
                    </td>
                    <td style={{ ...TD, textAlign: 'center' }}>{c.weight}</td>
                    {c.levels.map((l) => (
                      <td key={l.id} style={{ ...TD, textAlign: 'center' }}>
                        <label style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, cursor: 'pointer' }}>
                          <input
                            type="radio"
                            name={`criterion-${c.id}`}
                            value={l.id}
                            checked={selectedLevelId === l.id}
                            onChange={() => setSelections((prev) => ({ ...prev, [c.id]: l.id }))}
                            disabled={gradeMutation.isPending}
                          />
                          {l.description && (
                            <span style={{ fontSize: 11, color: 'var(--color-text-secondary)', maxWidth: 120, textAlign: 'center' }}>{l.description}</span>
                          )}
                        </label>
                      </td>
                    ))}
                    <td style={{ ...TD, textAlign: 'center', fontWeight: 600 }}>
                      {selectedLevelId ? rowScore : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
            <tfoot>
              <tr style={{ background: 'var(--color-surface)', fontWeight: 700 }}>
                <td style={TD} colSpan={2}>{t('rubrics.total')}</td>
                {rubric.criteria[0]?.levels.map((_, li) => <td key={li} style={TD} />)}
                <td style={{ ...TD, textAlign: 'center', fontSize: 15 }}>
                  {totalScore} / {maxScore}
                  {allSelected && <span style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginLeft: 6 }}>({pct}%)</span>}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          disabled={gradeMutation.isPending || !studentId.trim() || !allSelected}
        >
          {gradeMutation.isPending ? t('app.loading') : t('rubrics.saveGrade')}
        </button>
      </form>

      {results.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <h2 style={{ fontSize: 16, marginBottom: 12 }}>{t('rubrics.previousResults')}</h2>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('rubrics.studentId')}</th>
                  <th>{t('rubrics.cols.score')}</th>
                  <th>{t('rubrics.percentage')}</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r) => (
                  <tr key={r.student_id}>
                    <td>{r.student_id}</td>
                    <td>{r.total_score} / {r.max_score}</td>
                    <td>{r.percentage}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

const TH: React.CSSProperties = {
  padding: '8px 10px',
  textAlign: 'left',
  borderBottom: '2px solid var(--color-border)',
  whiteSpace: 'nowrap',
};

const TD: React.CSSProperties = {
  padding: '8px 10px',
  verticalAlign: 'top',
};
