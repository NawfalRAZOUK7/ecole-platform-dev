import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { useCreateRubric, useRubric, useUpdateRubric } from '../model/useRubrics';
import type { CreateRubricPayload, RubricLevel } from '../model/rubrics.types';

type EditLevel = Omit<RubricLevel, 'id'> & { id?: string };
type EditCriterion = { id?: string; name: string; weight: number; levels: EditLevel[] };

const DEFAULT_LEVELS: EditLevel[] = [
  { label: 'Excellent', score: 4, description: '' },
  { label: 'Bien', score: 3, description: '' },
  { label: 'Satisfaisant', score: 2, description: '' },
  { label: 'Insuffisant', score: 1, description: '' },
];

function makeEmptyCriterion(): EditCriterion {
  return {
    name: '',
    weight: 1,
    levels: DEFAULT_LEVELS.map((l) => ({ ...l })),
  };
}

function toPayload(
  title: string,
  subject: string,
  description: string,
  criteria: EditCriterion[],
): CreateRubricPayload {
  return {
    title,
    subject: subject || null,
    description: description || null,
    criteria: criteria.map((c) => ({
      name: c.name,
      weight: c.weight,
      levels: c.levels.map((l) => ({ label: l.label, score: l.score, description: l.description })),
    })),
  };
}

export function RubricEditorPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isNew = !id || id === 'new';

  const rubricQuery = useRubric(isNew ? '' : id!);
  const createMutation = useCreateRubric();
  const updateMutation = useUpdateRubric();

  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [criteria, setCriteria] = useState<EditCriterion[]>([makeEmptyCriterion()]);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (rubricQuery.data) {
      const r = rubricQuery.data;
      setTitle(r.title);
      setSubject(r.subject ?? '');
      setDescription(r.description ?? '');
      setCriteria(
        r.criteria.map((c) => ({
          id: c.id,
          name: c.name,
          weight: c.weight,
          levels: c.levels.map((l) => ({
            id: l.id,
            label: l.label,
            score: l.score,
            description: l.description,
          })),
        })),
      );
    }
  }, [rubricQuery.data]);

  function addCriterion() {
    setCriteria((prev) => [...prev, makeEmptyCriterion()]);
  }

  function removeCriterion(index: number) {
    setCriteria((prev) => prev.filter((_, i) => i !== index));
  }

  function updateCriterion(index: number, field: keyof EditCriterion, value: unknown) {
    setCriteria((prev) => prev.map((c, i) => (i === index ? { ...c, [field]: value } : c)));
  }

  function updateLevel(
    criterionIndex: number,
    levelIndex: number,
    field: keyof EditLevel,
    value: string | number,
  ) {
    setCriteria((prev) =>
      prev.map((c, ci) => {
        if (ci !== criterionIndex) return c;
        const levels = c.levels.map((l, li) => (li === levelIndex ? { ...l, [field]: value } : l));
        return { ...c, levels };
      }),
    );
  }

  function addLevel(criterionIndex: number) {
    setCriteria((prev) =>
      prev.map((c, ci) => {
        if (ci !== criterionIndex) return c;
        return { ...c, levels: [...c.levels, { label: '', score: 0, description: '' }] };
      }),
    );
  }

  function removeLevel(criterionIndex: number, levelIndex: number) {
    setCriteria((prev) =>
      prev.map((c, ci) => {
        if (ci !== criterionIndex) return c;
        return { ...c, levels: c.levels.filter((_, li) => li !== levelIndex) };
      }),
    );
  }

  async function handleSave() {
    setError(null);
    setSaved(false);
    const payload = toPayload(title, subject, description, criteria);
    try {
      if (isNew) {
        const created = await createMutation.mutateAsync(payload);
        navigate(`/rubrics/${created.id}/edit`, { replace: true });
      } else {
        await updateMutation.mutateAsync({ id: id!, ...payload });
        setSaved(true);
        window.setTimeout(() => setSaved(false), 2000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    }
  }

  if (!isNew && rubricQuery.isLoading) return <LoadingState />;

  const isSaving = createMutation.isPending || updateMutation.isPending;
  const levelCount = criteria[0]?.levels.length ?? 4;

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{isNew ? t('rubrics.create') : t('rubrics.edit')}</h1>
          <p className="page-subtitle">{t('rubrics.editorSubtitle')}</p>
        </div>
        <div className="page-actions">
          <button type="button" className="btn btn-secondary" onClick={() => navigate('/rubrics')}>
            {t('app.back')}
          </button>
          {!isNew && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => navigate(`/rubrics/${id}/grade`)}
            >
              {t('rubrics.grade')}
            </button>
          )}
          <button
            type="button"
            className="btn btn-primary"
            disabled={isSaving || !title.trim()}
            onClick={() => void handleSave()}
          >
            {isSaving ? t('app.loading') : saved ? t('app.saved') : t('app.save')}
          </button>
        </div>
      </div>

      <ErrorBanner
        error={error ?? (rubricQuery.error instanceof Error ? rubricQuery.error.message : null)}
        onDismiss={() => setError(null)}
      />

      <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
        <div className="form-field" style={{ flex: 2, minWidth: 200 }}>
          <label>{t('rubrics.cols.title')}</label>
          <input
            className="input"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>
        <div className="form-field" style={{ flex: 1, minWidth: 140 }}>
          <label>
            {t('rubrics.cols.subject')}{' '}
            <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
              ({t('app.optional')})
            </span>
          </label>
          <input className="input" value={subject} onChange={(e) => setSubject(e.target.value)} />
        </div>
        <div className="form-field" style={{ flex: 2, minWidth: 200 }}>
          <label>
            {t('rubrics.cols.description')}{' '}
            <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
              ({t('app.optional')})
            </span>
          </label>
          <input
            className="input"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ background: 'var(--color-surface)' }}>
              <th style={TH_STYLE}>{t('rubrics.criterion')}</th>
              <th style={{ ...TH_STYLE, width: 60 }}>{t('rubrics.weight')}</th>
              {(criteria[0]?.levels ?? []).map((l, li) => (
                <th key={li} style={TH_STYLE}>
                  <input
                    className="input"
                    style={{ fontSize: 12, padding: '4px 6px' }}
                    placeholder={t('rubrics.levelLabel')}
                    value={l.label}
                    onChange={(e) =>
                      criteria.forEach((_, ci) => updateLevel(ci, li, 'label', e.target.value))
                    }
                  />
                  <input
                    type="number"
                    className="input"
                    style={{ fontSize: 12, padding: '4px 6px', marginTop: 4, width: 60 }}
                    placeholder={t('rubrics.levelScore')}
                    value={l.score}
                    onChange={(e) =>
                      criteria.forEach((_, ci) =>
                        updateLevel(ci, li, 'score', Number(e.target.value)),
                      )
                    }
                  />
                  {levelCount > 2 && (
                    <button
                      type="button"
                      style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: 11,
                        color: 'var(--color-danger)',
                      }}
                      onClick={() => criteria.forEach((_, ci) => removeLevel(ci, li))}
                    >
                      ✕
                    </button>
                  )}
                </th>
              ))}
              <th style={TH_STYLE}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ padding: '4px 8px', fontSize: 12 }}
                  onClick={() => criteria.forEach((_, ci) => addLevel(ci))}
                >
                  + {t('rubrics.addLevel')}
                </button>
              </th>
              <th style={TH_STYLE}></th>
            </tr>
          </thead>
          <tbody>
            {criteria.map((c, ci) => (
              <tr key={ci} style={{ borderBottom: '1px solid var(--color-border)' }}>
                <td style={TD_STYLE}>
                  <input
                    className="input"
                    placeholder={t('rubrics.criterionName')}
                    value={c.name}
                    onChange={(e) => updateCriterion(ci, 'name', e.target.value)}
                  />
                </td>
                <td style={TD_STYLE}>
                  <input
                    type="number"
                    className="input"
                    style={{ width: 56 }}
                    min={1}
                    value={c.weight}
                    onChange={(e) => updateCriterion(ci, 'weight', Number(e.target.value))}
                  />
                </td>
                {c.levels.map((l, li) => (
                  <td key={li} style={TD_STYLE}>
                    <textarea
                      className="input"
                      rows={2}
                      style={{ resize: 'none', fontSize: 12 }}
                      placeholder={t('rubrics.levelDescription')}
                      value={l.description}
                      onChange={(e) => updateLevel(ci, li, 'description', e.target.value)}
                    />
                  </td>
                ))}
                <td style={TD_STYLE}></td>
                <td style={TD_STYLE}>
                  {criteria.length > 1 && (
                    <button
                      type="button"
                      className="btn btn-secondary"
                      style={{ padding: '4px 8px', fontSize: 12 }}
                      onClick={() => removeCriterion(ci)}
                    >
                      ✕
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <button
        type="button"
        className="btn btn-secondary"
        style={{ marginTop: 12 }}
        onClick={addCriterion}
      >
        + {t('rubrics.addCriterion')}
      </button>
    </div>
  );
}

const TH_STYLE: React.CSSProperties = {
  padding: '8px 10px',
  textAlign: 'left',
  borderBottom: '2px solid var(--color-border)',
  whiteSpace: 'nowrap',
  verticalAlign: 'bottom',
};

const TD_STYLE: React.CSSProperties = {
  padding: '8px 10px',
  verticalAlign: 'top',
};
