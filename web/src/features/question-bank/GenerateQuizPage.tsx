import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { Badge } from '@/shared/ui/Badge';
import { useCreateQuestion, useGenerateQuiz } from './useQuestionBank';
import type { DifficultyLevel, GenerateQuizParams, Question, QuestionType } from './question-bank.types';

const DIFFICULTY_LEVELS: DifficultyLevel[] = ['easy', 'medium', 'hard'];

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

const DEFAULT_PARAMS: GenerateQuizParams = {
  subject: '',
  difficulty: undefined,
  count: 10,
  tags: [],
};

export function GenerateQuizPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const generateMutation = useGenerateQuiz();
  const createMutation = useCreateQuestion();

  const [params, setParams] = useState<GenerateQuizParams>(DEFAULT_PARAMS);
  const [generatedQuestions, setGeneratedQuestions] = useState<Question[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setGeneratedQuestions(null);
    setSaved(false);
    try {
      const result = await generateMutation.mutateAsync(params);
      setGeneratedQuestions(result.questions);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    }
  }

  async function handleSaveAll() {
    if (!generatedQuestions) return;
    setError(null);
    try {
      await Promise.all(
        generatedQuestions.map((q) =>
          createMutation.mutateAsync({
            subject: q.subject,
            type: q.type,
            difficulty: q.difficulty,
            text: q.text,
            choices: q.choices,
            correct_answer: q.correct_answer,
            tags: q.tags,
          })
        )
      );
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    }
  }

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('questionBank.generate.title')}</h1>
          <p className="page-subtitle">{t('questionBank.generate.subtitle')}</p>
        </div>
        <button type="button" className="btn btn-secondary" onClick={() => navigate('/question-bank')}>
          {t('app.back')}
        </button>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <div className="card" style={{ maxWidth: 480, padding: 24, marginBottom: 24 }}>
        <form onSubmit={handleGenerate}>
          <div className="form-field">
            <label htmlFor="gen-subject">{t('questionBank.cols.subject')}</label>
            <input
              id="gen-subject"
              className="input"
              required
              value={params.subject}
              onChange={(e) => setParams((p) => ({ ...p, subject: e.target.value }))}
              disabled={generateMutation.isPending}
            />
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            <div className="form-field" style={{ flex: 1 }}>
              <label>{t('questionBank.cols.difficulty')} <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>({t('app.optional')})</span></label>
              <select
                className="input"
                value={params.difficulty ?? ''}
                onChange={(e) => setParams((p) => ({ ...p, difficulty: (e.target.value as DifficultyLevel) || undefined }))}
                disabled={generateMutation.isPending}
              >
                <option value="">{t('questionBank.allDifficulties')}</option>
                {DIFFICULTY_LEVELS.map((d) => (
                  <option key={d} value={d}>{t(`questionBank.difficulty.${d}`)}</option>
                ))}
              </select>
            </div>
            <div className="form-field" style={{ flex: 1 }}>
              <label>{t('questionBank.generate.count')}</label>
              <input
                type="number"
                className="input"
                min={1}
                max={50}
                required
                value={params.count}
                onChange={(e) => setParams((p) => ({ ...p, count: Number(e.target.value) }))}
                disabled={generateMutation.isPending}
              />
            </div>
          </div>
          <div className="form-field">
            <label>{t('questionBank.tags')} <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>({t('app.optional')})</span></label>
            <input
              className="input"
              placeholder={t('questionBank.tagsPlaceholder')}
              value={(params.tags ?? []).join(', ')}
              onChange={(e) => setParams((p) => ({ ...p, tags: e.target.value.split(',').map((s) => s.trim()).filter(Boolean) }))}
              disabled={generateMutation.isPending}
            />
          </div>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={generateMutation.isPending || !params.subject.trim()}
          >
            {generateMutation.isPending ? t('app.loading') : t('questionBank.generate.submit')}
          </button>
        </form>
      </div>

      {generatedQuestions && generatedQuestions.length > 0 && (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h2 style={{ fontSize: 16 }}>
              {t('questionBank.generate.previewTitle', { count: generatedQuestions.length })}
            </h2>
            {!saved ? (
              <button
                type="button"
                className="btn btn-primary"
                disabled={createMutation.isPending}
                onClick={() => void handleSaveAll()}
              >
                {createMutation.isPending ? t('app.loading') : t('questionBank.generate.saveAll')}
              </button>
            ) : (
              <Badge variant="success">{t('app.saved')}</Badge>
            )}
          </div>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('questionBank.cols.text')}</th>
                  <th>{t('questionBank.cols.type')}</th>
                  <th>{t('questionBank.cols.difficulty')}</th>
                  <th>{t('questionBank.cols.tags')}</th>
                </tr>
              </thead>
              <tbody>
                {generatedQuestions.map((q, i) => (
                  <tr key={q.id ?? i}>
                    <td style={{ maxWidth: 380, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{q.text}</td>
                    <td>
                      <Badge variant={TYPE_VARIANT[q.type]}>{t(`questionBank.types.${q.type}`)}</Badge>
                    </td>
                    <td>
                      <Badge variant={DIFFICULTY_VARIANT[q.difficulty]}>{t(`questionBank.difficulty.${q.difficulty}`)}</Badge>
                    </td>
                    <td style={{ fontSize: 12 }}>{q.tags.join(', ') || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
