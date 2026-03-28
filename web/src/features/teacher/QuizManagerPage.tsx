/**
 * Teacher Quiz Manager — create class-specific quizzes, assign platform quizzes.
 *
 * Phase 10B — Teacher creates school-scoped quizzes and assigns published
 * platform quizzes to assignments.
 * API: POST /quizzes, GET /quizzes, PUT /quizzes/{id}, POST /quizzes/{id}/publish
 */

import { useMemo, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { useCreateQuiz, usePublishQuiz, useTeacherQuizzes } from './useTeacher';
import type { QuestionInput, Quiz } from './teacher.service';

interface McqOptions {
  choices?: string[];
}

type View = 'list' | 'create';

export function QuizManagerPage() {
  const { t } = useTranslation();
  const [view, setView] = useState<View>('list');

  const quizzesQuery = useTeacherQuizzes();
  const createQuizMutation = useCreateQuiz();
  const publishQuizMutation = usePublishQuiz();
  const quizzes: Quiz[] = useMemo(
    () => quizzesQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [quizzesQuery.data]
  );
  const dismissibleError = useDismissibleError(
    useMemo(
      () => toBannerError(quizzesQuery.error ?? createQuizMutation.error ?? publishQuizMutation.error, t('app.error')),
      [createQuizMutation.error, publishQuizMutation.error, quizzesQuery.error, t]
    )
  );

  async function handlePublish(quizId: string) {
    await publishQuizMutation.mutateAsync(quizId);
    await quizzesQuery.refetch();
  }

  if (quizzesQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('teacherQuiz.title')}</h1>
      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void quizzesQuery.refetch()}
      />

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
            <>
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
                    {quizzes.map((quiz) => (
                      <tr key={quiz.id}>
                        <td style={{ fontWeight: 600 }}>{quiz.title}</td>
                        <td>{quiz.subject ? t(`cms.subjects.${quiz.subject}`, quiz.subject) : '—'}</td>
                        <td>{quiz.difficulty}</td>
                        <td>{quiz.question_count}</td>
                        <td>{quiz.total_points}</td>
                        <td><span className={`status-badge status-${quiz.status}`}>{quiz.status}</span></td>
                        <td>
                          {quiz.status === 'draft' && quiz.school_id && (
                            <button
                              className="btn btn-primary"
                              style={{ fontSize: 12, padding: '4px 10px' }}
                              onClick={() => void handlePublish(quiz.id)}
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

              {quizzesQuery.hasNextPage && (
                <div style={{ textAlign: 'center', marginTop: 16 }}>
                  <button className="btn btn-secondary" onClick={() => void quizzesQuery.fetchNextPage()} disabled={quizzesQuery.isFetchingNextPage}>
                    {quizzesQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
                  </button>
                </div>
              )}
            </>
          )}
        </>
      )}

      {view === 'create' && (
        <QuizCreateForm
          onCancel={() => setView('list')}
          onCreated={async () => {
            setView('list');
            await quizzesQuery.refetch();
          }}
        />
      )}
    </div>
  );
}

function QuizCreateForm({
  onCancel,
  onCreated,
}: {
  onCancel: () => void;
  onCreated: () => Promise<void>;
}) {
  const { t } = useTranslation();
  const createQuizMutation = useCreateQuiz();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [subject, setSubject] = useState('');
  const [levelBand] = useState('');
  const [difficulty, setDifficulty] = useState('easy');
  const [timeLimit, setTimeLimit] = useState('');
  const [maxAttempts, setMaxAttempts] = useState('3');
  const [shuffle, setShuffle] = useState(false);
  const [questions, setQuestions] = useState<QuestionInput[]>([]);

  function addQuestion(type: string) {
    const question: QuestionInput = {
      question_type: type,
      question_text: '',
      options: type === 'mcq' ? { choices: ['', ''] } : null,
      correct_answer: type === 'true_false' ? true : type === 'mcq' ? 0 : '',
      points: 1,
      order: questions.length,
      explanation: '',
    };
    setQuestions([...questions, question]);
  }

  function updateQuestion<K extends keyof QuestionInput>(index: number, field: K, value: QuestionInput[K]) {
    const next = [...questions];
    next[index] = { ...next[index], [field]: value };
    setQuestions(next);
  }

  function removeQuestion(index: number) {
    setQuestions(questions.filter((_, itemIndex) => itemIndex !== index));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!title.trim() || questions.length === 0) return;

    await createQuizMutation.mutateAsync({
      title: title.trim(),
      description: description.trim() || null,
      subject: subject || null,
      level_band: levelBand || null,
      difficulty,
      time_limit_minutes: timeLimit ? parseInt(timeLimit, 10) : null,
      max_attempts: parseInt(maxAttempts, 10) || 3,
      shuffle_questions: shuffle,
      questions: questions.map((question, index) => ({
        ...question,
        order: index,
      })),
    });
    await onCreated();
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
            {['math', 'french', 'arabic', 'science', 'history', 'geography', 'english'].map((item) => (
              <option key={item} value={item}>{t(`cms.subjects.${item}`, item)}</option>
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

      <div className="form-field" style={{ marginBottom: 16 }}>
        <label>{t('teacherQuiz.description')}</label>
        <input className="filter-input" value={description} onChange={(e) => setDescription(e.target.value)} style={{ width: '100%' }} />
      </div>

      <h4 style={{ margin: '0 0 8px' }}>{t('teacherQuiz.questions')} ({questions.length})</h4>

      {questions.map((question, index) => (
        <div key={index} className="card" style={{ padding: 12, marginBottom: 12, background: 'var(--color-bg)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{ fontWeight: 600, fontSize: 13 }}>
              Q{index + 1} — {t(`teacherQuiz.type_${question.question_type}`, question.question_type)}
            </span>
            <button type="button" className="btn btn-danger" style={{ fontSize: 11, padding: '2px 8px' }} onClick={() => removeQuestion(index)}>
              {t('teacherQuiz.remove')}
            </button>
          </div>
          <div className="form-field" style={{ marginBottom: 8 }}>
            <input
              className="filter-input"
              placeholder={t('teacherQuiz.questionText')}
              value={question.question_text}
              onChange={(e) => updateQuestion(index, 'question_text', e.target.value)}
              required
              style={{ width: '100%' }}
            />
          </div>
          <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
            <div className="form-field">
              <label style={{ fontSize: 11 }}>{t('teacherQuiz.points')}</label>
              <input type="number" className="filter-input" value={question.points} onChange={(e) => updateQuestion(index, 'points', parseInt(e.target.value, 10) || 1)} min="1" style={{ width: 60 }} />
            </div>
          </div>

          {question.question_type === 'mcq' && (
            <div style={{ marginBottom: 8 }}>
              {((question.options as McqOptions | null)?.choices || []).map((choice: string, choiceIndex: number) => (
                <div key={choiceIndex} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                  <input
                    type="radio"
                    name={`q${index}_correct`}
                    checked={question.correct_answer === choiceIndex}
                    onChange={() => updateQuestion(index, 'correct_answer', choiceIndex)}
                  />
                  <input
                    className="filter-input"
                    value={choice}
                    onChange={(e) => {
                      const choices = [...((question.options as McqOptions | null)?.choices || [])];
                      choices[choiceIndex] = e.target.value;
                      updateQuestion(index, 'options', { choices });
                    }}
                    placeholder={`${t('teacherQuiz.option')} ${choiceIndex + 1}`}
                    style={{ flex: 1 }}
                  />
                </div>
              ))}
              <button
                type="button"
                className="btn btn-secondary"
                style={{ fontSize: 11, padding: '2px 8px', marginTop: 4 }}
                onClick={() => {
                  const choices = [...((question.options as McqOptions | null)?.choices || []), ''];
                  updateQuestion(index, 'options', { choices });
                }}
              >
                + {t('teacherQuiz.addOption')}
              </button>
            </div>
          )}

          {question.question_type === 'true_false' && (
            <div style={{ display: 'flex', gap: 12, marginBottom: 8 }}>
              <label><input type="radio" checked={question.correct_answer === true} onChange={() => updateQuestion(index, 'correct_answer', true)} /> {t('teacherQuiz.true')}</label>
              <label><input type="radio" checked={question.correct_answer === false} onChange={() => updateQuestion(index, 'correct_answer', false)} /> {t('teacherQuiz.false')}</label>
            </div>
          )}

          {question.question_type === 'fill_in_blank' && (
            <div className="form-field" style={{ marginBottom: 8 }}>
              <label style={{ fontSize: 11 }}>{t('teacherQuiz.correctAnswer')}</label>
              <input
                className="filter-input"
                value={typeof question.correct_answer === 'string' ? question.correct_answer : ''}
                onChange={(e) => updateQuestion(index, 'correct_answer', e.target.value)}
                style={{ width: '100%' }}
              />
            </div>
          )}

          <div className="form-field">
            <input
              className="filter-input"
              placeholder={t('teacherQuiz.explanation')}
              value={question.explanation}
              onChange={(e) => updateQuestion(index, 'explanation', e.target.value)}
              style={{ width: '100%', fontSize: 12 }}
            />
          </div>
        </div>
      ))}

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
        <button type="submit" className="btn btn-primary" disabled={createQuizMutation.isPending || !title.trim() || questions.length === 0}>
          {createQuizMutation.isPending ? t('app.loading') : t('teacherQuiz.save')}
        </button>
        <button type="button" className="btn btn-secondary" onClick={onCancel}>
          {t('app.cancel')}
        </button>
      </div>
    </form>
  );
}
