/**
 * Teacher Quiz Manager — create class-specific quizzes, assign platform quizzes.
 *
 * Phase 10B — Teacher creates school-scoped quizzes and assigns published
 * platform quizzes to assignments.
 * API: POST /quizzes, GET /quizzes, PUT /quizzes/{id}, POST /quizzes/{id}/publish
 */

import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { LoadingState } from '@/shared/ui/LoadingState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { EmptyState } from '@/shared/ui/EmptyState';

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */
interface Quiz {
  id: string;
  school_id: string | null;
  title: string;
  description: string | null;
  subject: string | null;
  level_band: string | null;
  difficulty: string;
  status: string;
  question_count: number;
  total_points: number;
  time_limit_minutes: number | null;
  max_attempts: number;
}

interface QuestionInput {
  question_type: string;
  question_text: string;
  options: Record<string, unknown> | null;
  correct_answer: unknown;
  points: number;
  order: number;
  explanation: string;
}

type View = 'list' | 'create';

/* ------------------------------------------------------------------ */
/* Main                                                                */
/* ------------------------------------------------------------------ */
export function QuizManagerPage() {
  const { t } = useTranslation();
  const [view, setView] = useState<View>('list');
  const [error, setError] = useState<string | null>(null);
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchQuizzes = useCallback(async () => {
    try {
      const resp = await api.list<Quiz>('/quizzes');
      setQuizzes(resp.data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [t]);

  useEffect(() => {
    setLoading(true);
    fetchQuizzes().finally(() => setLoading(false));
  }, [fetchQuizzes]);

  async function handlePublish(quizId: string) {
    try {
      await api.post(`/quizzes/${quizId}/publish`);
      await fetchQuizzes();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('teacherQuiz.title')}</h1>
      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={fetchQuizzes} />

      {view === 'list' && (
        <>
          <div className="filters-bar" style={{ marginBottom: 16 }}>
            <button className="btn btn-primary" onClick={() => setView('create')}>
              {t('teacherQuiz.create')}
            </button>
          </div>

          {quizzes.length === 0 ? (
            <EmptyState message={t('teacherQuiz.empty')} />
          ) : (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>{t('teacherQuiz.quizTitle')}</th>
                    <th>{t('teacherQuiz.subject')}</th>
                    <th>{t('teacherQuiz.difficulty')}</th>
                    <th>{t('teacherQuiz.questions')}</th>
                    <th>{t('teacherQuiz.points')}</th>
                    <th>{t('teacherQuiz.status')}</th>
                    <th>{t('teacherQuiz.actions')}</th>
                  </tr>
                </thead>
                <tbody>
                  {quizzes.map((q) => (
                    <tr key={q.id}>
                      <td style={{ fontWeight: 600 }}>{q.title}</td>
                      <td>{q.subject ? t(`cms.subjects.${q.subject}`, q.subject) : '—'}</td>
                      <td>{q.difficulty}</td>
                      <td>{q.question_count}</td>
                      <td>{q.total_points}</td>
                      <td>
                        <span className={`status-badge status-${q.status}`}>
                          {q.status}
                        </span>
                      </td>
                      <td>
                        {q.status === 'draft' && q.school_id && (
                          <button
                            className="btn btn-primary"
                            style={{ fontSize: 12, padding: '4px 10px' }}
                            onClick={() => handlePublish(q.id)}
                          >
                            {t('teacherQuiz.publish')}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {view === 'create' && (
        <QuizCreateForm
          onCancel={() => setView('list')}
          onCreated={() => { setView('list'); fetchQuizzes(); }}
          onError={setError}
        />
      )}
    </div>
  );
}

/* ================================================================== */
/* Quick Create Form — simplified for teacher (no drag-drop editors)  */
/* ================================================================== */
function QuizCreateForm({
  onCancel,
  onCreated,
  onError,
}: {
  onCancel: () => void;
  onCreated: () => void;
  onError: (e: string | null) => void;
}) {
  const { t } = useTranslation();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [subject, setSubject] = useState('');
  const [levelBand, setLevelBand] = useState('');
  const [difficulty, setDifficulty] = useState('easy');
  const [timeLimit, setTimeLimit] = useState('');
  const [maxAttempts, setMaxAttempts] = useState('3');
  const [shuffle, setShuffle] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Questions
  const [questions, setQuestions] = useState<QuestionInput[]>([]);

  function addQuestion(type: string) {
    const q: QuestionInput = {
      question_type: type,
      question_text: '',
      options: type === 'mcq' ? { choices: ['', ''] } : null,
      correct_answer: type === 'true_false' ? true : type === 'mcq' ? 0 : '',
      points: 1,
      order: questions.length,
      explanation: '',
    };
    setQuestions([...questions, q]);
  }

  function updateQuestion(idx: number, field: string, value: unknown) {
    const copy = [...questions];
    (copy[idx] as any)[field] = value;
    setQuestions(copy);
  }

  function removeQuestion(idx: number) {
    setQuestions(questions.filter((_, i) => i !== idx));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!title.trim() || questions.length === 0) return;
    setSubmitting(true);
    try {
      await api.post('/quizzes', {
        title: title.trim(),
        description: description.trim() || null,
        subject: subject || null,
        level_band: levelBand || null,
        difficulty,
        time_limit_minutes: timeLimit ? parseInt(timeLimit, 10) : null,
        max_attempts: parseInt(maxAttempts, 10) || 3,
        shuffle_questions: shuffle,
        questions: questions.map((q, i) => ({
          ...q,
          order: i,
        })),
      });
      onCreated();
    } catch (err) {
      onError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="card" style={{ padding: 20, maxWidth: 700 }} onSubmit={handleSubmit}>
      <h3 style={{ margin: '0 0 16px' }}>{t('teacherQuiz.createTitle')}</h3>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
        <div className="form-field">
          <label>{t('teacherQuiz.quizTitle')}</label>
          <input className="filter-input" value={title} onChange={(e) => setTitle(e.target.value)} required style={{ width: '100%' }} />
        </div>
        <div className="form-field">
          <label>{t('teacherQuiz.subject')}</label>
          <select className="filter-select" value={subject} onChange={(e) => setSubject(e.target.value)} style={{ width: '100%' }}>
            <option value="">—</option>
            {['math', 'french', 'arabic', 'science', 'history', 'geography', 'english'].map((s) => (
              <option key={s} value={s}>{t(`cms.subjects.${s}`, s)}</option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label>{t('teacherQuiz.difficulty')}</label>
          <select className="filter-select" value={difficulty} onChange={(e) => setDifficulty(e.target.value)} style={{ width: '100%' }}>
            <option value="easy">{t('teacherQuiz.easy')}</option>
            <option value="medium">{t('teacherQuiz.medium')}</option>
            <option value="hard">{t('teacherQuiz.hard')}</option>
          </select>
        </div>
        <div className="form-field">
          <label>{t('teacherQuiz.timeLimit')}</label>
          <input type="number" className="filter-input" value={timeLimit} onChange={(e) => setTimeLimit(e.target.value)} placeholder="min" min="0" style={{ width: '100%' }} />
        </div>
        <div className="form-field">
          <label>{t('teacherQuiz.maxAttempts')}</label>
          <input type="number" className="filter-input" value={maxAttempts} onChange={(e) => setMaxAttempts(e.target.value)} min="1" style={{ width: '100%' }} />
        </div>
        <div className="form-field" style={{ display: 'flex', alignItems: 'center', gap: 8, paddingTop: 24 }}>
          <input type="checkbox" checked={shuffle} onChange={(e) => setShuffle(e.target.checked)} />
          <label style={{ margin: 0 }}>{t('teacherQuiz.shuffle')}</label>
        </div>
      </div>

      {description !== undefined && (
        <div className="form-field" style={{ marginBottom: 16 }}>
          <label>{t('teacherQuiz.description')}</label>
          <input className="filter-input" value={description} onChange={(e) => setDescription(e.target.value)} style={{ width: '100%' }} />
        </div>
      )}

      {/* Questions */}
      <h4 style={{ margin: '0 0 8px' }}>{t('teacherQuiz.questions')} ({questions.length})</h4>

      {questions.map((q, idx) => (
        <div key={idx} className="card" style={{ padding: 12, marginBottom: 12, background: 'var(--color-bg)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{ fontWeight: 600, fontSize: 13 }}>
              Q{idx + 1} — {t(`teacherQuiz.type_${q.question_type}`, q.question_type)}
            </span>
            <button type="button" className="btn btn-danger" style={{ fontSize: 11, padding: '2px 8px' }} onClick={() => removeQuestion(idx)}>
              {t('teacherQuiz.remove')}
            </button>
          </div>
          <div className="form-field" style={{ marginBottom: 8 }}>
            <input
              className="filter-input"
              placeholder={t('teacherQuiz.questionText')}
              value={q.question_text}
              onChange={(e) => updateQuestion(idx, 'question_text', e.target.value)}
              required
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
            <div className="form-field">
              <label style={{ fontSize: 11 }}>{t('teacherQuiz.points')}</label>
              <input type="number" className="filter-input" value={q.points} onChange={(e) => updateQuestion(idx, 'points', parseInt(e.target.value, 10) || 1)} min="1" style={{ width: 60 }} />
            </div>
          </div>

          {/* MCQ options */}
          {q.question_type === 'mcq' && (
            <div style={{ marginBottom: 8 }}>
              {((q.options as any)?.choices || []).map((c: string, ci: number) => (
                <div key={ci} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                  <input
                    type="radio"
                    name={`q${idx}_correct`}
                    checked={q.correct_answer === ci}
                    onChange={() => updateQuestion(idx, 'correct_answer', ci)}
                  />
                  <input
                    className="filter-input"
                    value={c}
                    onChange={(e) => {
                      const choices = [...(q.options as any).choices];
                      choices[ci] = e.target.value;
                      updateQuestion(idx, 'options', { choices });
                    }}
                    placeholder={`${t('teacherQuiz.option')} ${ci + 1}`}
                    style={{ flex: 1 }}
                  />
                </div>
              ))}
              <button
                type="button"
                className="btn btn-secondary"
                style={{ fontSize: 11, padding: '2px 8px', marginTop: 4 }}
                onClick={() => {
                  const choices = [...(q.options as any).choices, ''];
                  updateQuestion(idx, 'options', { choices });
                }}
              >
                + {t('teacherQuiz.addOption')}
              </button>
            </div>
          )}

          {/* True/False */}
          {q.question_type === 'true_false' && (
            <div style={{ display: 'flex', gap: 12, marginBottom: 8 }}>
              <label><input type="radio" checked={q.correct_answer === true} onChange={() => updateQuestion(idx, 'correct_answer', true)} /> {t('teacherQuiz.true')}</label>
              <label><input type="radio" checked={q.correct_answer === false} onChange={() => updateQuestion(idx, 'correct_answer', false)} /> {t('teacherQuiz.false')}</label>
            </div>
          )}

          {/* Fill-in */}
          {q.question_type === 'fill_in_blank' && (
            <div className="form-field" style={{ marginBottom: 8 }}>
              <label style={{ fontSize: 11 }}>{t('teacherQuiz.correctAnswer')}</label>
              <input
                className="filter-input"
                value={typeof q.correct_answer === 'string' ? q.correct_answer : ''}
                onChange={(e) => updateQuestion(idx, 'correct_answer', e.target.value)}
                style={{ width: '100%' }}
              />
            </div>
          )}

          <div className="form-field">
            <input
              className="filter-input"
              placeholder={t('teacherQuiz.explanation')}
              value={q.explanation}
              onChange={(e) => updateQuestion(idx, 'explanation', e.target.value)}
              style={{ width: '100%', fontSize: 12 }}
            />
          </div>
        </div>
      ))}

      {/* Add question buttons */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 16, flexWrap: 'wrap' }}>
        {[
          { type: 'mcq', label: t('teacherQuiz.type_mcq') },
          { type: 'true_false', label: t('teacherQuiz.type_true_false') },
          { type: 'fill_in_blank', label: t('teacherQuiz.type_fill_in_blank') },
        ].map(({ type, label }) => (
          <button key={type} type="button" className="btn btn-secondary" style={{ fontSize: 12 }} onClick={() => addQuestion(type)}>
            + {label}
          </button>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        <button type="submit" className="btn btn-primary" disabled={submitting || !title.trim() || questions.length === 0}>
          {submitting ? t('app.loading') : t('teacherQuiz.save')}
        </button>
        <button type="button" className="btn btn-secondary" onClick={onCancel}>
          {t('app.cancel')}
        </button>
      </div>
    </form>
  );
}
