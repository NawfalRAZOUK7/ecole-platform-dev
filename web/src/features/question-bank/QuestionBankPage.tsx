import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/services/auth/AuthContext';
import { Badge } from '@/shared/ui/Badge';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { useCreateQuestion, useQuestionBankStats, useQuestions } from './useQuestionBank';
import type { CreateQuestionPayload, DifficultyLevel, QuestionType } from './question-bank.types';

const TYPE_VARIANT: Record<QuestionType, 'info' | 'success' | 'warning' | 'neutral'> = {
  mcq: 'info',
  true_false: 'success',
  short_answer: 'warning',
  essay: 'neutral',
};

const DIFFICULTY_VARIANT: Record<DifficultyLevel, 'success' | 'warning' | 'error'> = {
  easy: 'success',
  medium: 'warning',
  hard: 'error',
};

const QUESTION_TYPES: QuestionType[] = ['mcq', 'true_false', 'short_answer', 'essay'];
const DIFFICULTY_LEVELS: DifficultyLevel[] = ['easy', 'medium', 'hard'];

const EMPTY_FORM: CreateQuestionPayload = {
  subject: '',
  type: 'mcq',
  difficulty: 'medium',
  text: '',
  choices: [
    { text: '', is_correct: true },
    { text: '', is_correct: false },
  ],
  tags: [],
};

export function QuestionBankPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const canCreate = ['TCH', 'ADM', 'DIR', 'CONTENT_MGR'].includes(user?.role ?? '');

  const [filterSubject, setFilterSubject] = useState('');
  const [filterType, setFilterType] = useState<QuestionType | ''>('');
  const [filterDifficulty, setFilterDifficulty] = useState<DifficultyLevel | ''>('');
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<CreateQuestionPayload>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);

  const questionsQuery = useQuestions({
    subject: filterSubject || undefined,
    type: filterType || undefined,
    difficulty: filterDifficulty || undefined,
  });
  const statsQuery = useQuestionBankStats();
  const createMutation = useCreateQuestion();

  const questions = questionsQuery.data?.data ?? [];
  const stats = statsQuery.data;

  function updateChoice(index: number, field: 'text' | 'is_correct', value: string | boolean) {
    setForm((prev) => {
      const choices = [...(prev.choices ?? [])];
      choices[index] = { ...choices[index], [field]: value };
      return { ...prev, choices };
    });
  }

  function addChoice() {
    setForm((prev) => ({
      ...prev,
      choices: [...(prev.choices ?? []), { text: '', is_correct: false }],
    }));
  }

  function removeChoice(index: number) {
    setForm((prev) => ({
      ...prev,
      choices: (prev.choices ?? []).filter((_, i) => i !== index),
    }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    try {
      await createMutation.mutateAsync(form);
      setShowModal(false);
      setForm(EMPTY_FORM);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : t('app.error'));
    }
  }

  if (questionsQuery.isLoading) return <LoadingState />;

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('questionBank.title')}</h1>
          <p className="page-subtitle">{t('questionBank.subtitle')}</p>
        </div>
        <div className="page-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => navigate('/question-bank/import')}
          >
            {t('questionBank.importFromQuiz')}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => navigate('/question-bank/generate')}
          >
            {t('questionBank.generateQuiz')}
          </button>
          {canCreate && (
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => setShowModal(true)}
            >
              {t('questionBank.addQuestion')}
            </button>
          )}
        </div>
      </div>

      {stats && (
        <div className="stats-row" style={{ display: 'flex', gap: 16, marginBottom: 16, flexWrap: 'wrap' }}>
          <div className="stat-card" style={{ padding: '12px 20px', background: 'var(--color-surface)', borderRadius: 8, border: '1px solid var(--color-border)' }}>
            <div style={{ fontSize: 24, fontWeight: 700 }}>{stats.total}</div>
            <div style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{t('questionBank.stats.total')}</div>
          </div>
          {DIFFICULTY_LEVELS.map((d) => (
            <div key={d} className="stat-card" style={{ padding: '12px 20px', background: 'var(--color-surface)', borderRadius: 8, border: '1px solid var(--color-border)' }}>
              <div style={{ fontSize: 24, fontWeight: 700 }}>{stats.by_difficulty[d] ?? 0}</div>
              <div style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{t(`questionBank.difficulty.${d}`)}</div>
            </div>
          ))}
        </div>
      )}

      <div className="filter-row" style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
        <input
          type="text"
          className="input"
          placeholder={t('questionBank.filterSubject')}
          value={filterSubject}
          onChange={(e) => setFilterSubject(e.target.value)}
          style={{ maxWidth: 200 }}
        />
        <select
          className="input"
          value={filterType}
          onChange={(e) => setFilterType(e.target.value as QuestionType | '')}
          style={{ maxWidth: 180 }}
        >
          <option value="">{t('questionBank.allTypes')}</option>
          {QUESTION_TYPES.map((qt) => (
            <option key={qt} value={qt}>{t(`questionBank.types.${qt}`)}</option>
          ))}
        </select>
        <select
          className="input"
          value={filterDifficulty}
          onChange={(e) => setFilterDifficulty(e.target.value as DifficultyLevel | '')}
          style={{ maxWidth: 180 }}
        >
          <option value="">{t('questionBank.allDifficulties')}</option>
          {DIFFICULTY_LEVELS.map((d) => (
            <option key={d} value={d}>{t(`questionBank.difficulty.${d}`)}</option>
          ))}
        </select>
      </div>

      <ErrorBanner error={questionsQuery.error instanceof Error ? questionsQuery.error.message : null} onRetry={() => void questionsQuery.refetch()} />

      {questions.length === 0 ? (
        <EmptyState message={t('questionBank.empty')} icon="❓" />
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('questionBank.cols.text')}</th>
                <th>{t('questionBank.cols.subject')}</th>
                <th>{t('questionBank.cols.type')}</th>
                <th>{t('questionBank.cols.difficulty')}</th>
                <th>{t('questionBank.cols.tags')}</th>
              </tr>
            </thead>
            <tbody>
              {questions.map((q) => (
                <tr key={q.id}>
                  <td style={{ maxWidth: 360, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{q.text}</td>
                  <td>{q.subject}</td>
                  <td>
                    <Badge variant={TYPE_VARIANT[q.type]}>
                      {t(`questionBank.types.${q.type}`)}
                    </Badge>
                  </td>
                  <td>
                    <Badge variant={DIFFICULTY_VARIANT[q.difficulty]}>
                      {t(`questionBank.difficulty.${q.difficulty}`)}
                    </Badge>
                  </td>
                  <td style={{ fontSize: 12 }}>{q.tags.join(', ') || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 560, width: '100%' }}>
            <h2 style={{ marginBottom: 16 }}>{t('questionBank.addQuestion')}</h2>
            <ErrorBanner error={formError} onDismiss={() => setFormError(null)} />
            <form onSubmit={handleSubmit}>
              <div className="form-field">
                <label>{t('questionBank.cols.subject')}</label>
                <input className="input" required value={form.subject} onChange={(e) => setForm((p) => ({ ...p, subject: e.target.value }))} />
              </div>
              <div style={{ display: 'flex', gap: 12 }}>
                <div className="form-field" style={{ flex: 1 }}>
                  <label>{t('questionBank.cols.type')}</label>
                  <select className="input" value={form.type} onChange={(e) => setForm((p) => ({ ...p, type: e.target.value as QuestionType }))}>
                    {QUESTION_TYPES.map((qt) => <option key={qt} value={qt}>{t(`questionBank.types.${qt}`)}</option>)}
                  </select>
                </div>
                <div className="form-field" style={{ flex: 1 }}>
                  <label>{t('questionBank.cols.difficulty')}</label>
                  <select className="input" value={form.difficulty} onChange={(e) => setForm((p) => ({ ...p, difficulty: e.target.value as DifficultyLevel }))}>
                    {DIFFICULTY_LEVELS.map((d) => <option key={d} value={d}>{t(`questionBank.difficulty.${d}`)}</option>)}
                  </select>
                </div>
              </div>
              <div className="form-field">
                <label>{t('questionBank.cols.text')}</label>
                <textarea className="input" required rows={3} value={form.text} onChange={(e) => setForm((p) => ({ ...p, text: e.target.value }))} style={{ resize: 'vertical' }} />
              </div>
              {(form.type === 'mcq' || form.type === 'true_false') && (
                <div className="form-field">
                  <label>{t('questionBank.choices')}</label>
                  {(form.choices ?? []).map((choice, i) => (
                    <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 6, alignItems: 'center' }}>
                      <input type="text" className="input" style={{ flex: 1 }} placeholder={t('questionBank.choiceText')} value={choice.text} onChange={(e) => updateChoice(i, 'text', e.target.value)} />
                      <label style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13, whiteSpace: 'nowrap' }}>
                        <input type="checkbox" checked={choice.is_correct} onChange={(e) => updateChoice(i, 'is_correct', e.target.checked)} />
                        {t('questionBank.correct')}
                      </label>
                      {(form.choices ?? []).length > 2 && (
                        <button type="button" className="btn btn-secondary" style={{ padding: '4px 8px' }} onClick={() => removeChoice(i)}>✕</button>
                      )}
                    </div>
                  ))}
                  {form.type === 'mcq' && (
                    <button type="button" className="btn btn-secondary" style={{ marginTop: 4 }} onClick={addChoice}>
                      + {t('questionBank.addChoice')}
                    </button>
                  )}
                </div>
              )}
              <div className="form-field">
                <label>{t('questionBank.tags')} <span style={{ color: 'var(--color-text-secondary)', fontSize: 12 }}>({t('app.optional')})</span></label>
                <input className="input" placeholder={t('questionBank.tagsPlaceholder')} value={(form.tags ?? []).join(', ')} onChange={(e) => setForm((p) => ({ ...p, tags: e.target.value.split(',').map((s) => s.trim()).filter(Boolean) }))} />
              </div>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 16 }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>{t('app.cancel')}</button>
                <button type="submit" className="btn btn-primary" disabled={createMutation.isPending}>{createMutation.isPending ? t('app.loading') : t('app.save')}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
