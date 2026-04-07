import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { Badge } from '@/shared/ui/Badge';
import { useImportFromQuiz } from './useQuestionBank';
import type { DifficultyLevel, Question, QuestionType } from './question-bank.types';

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

export function QuestionBankImportPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const importMutation = useImportFromQuiz();

  const [quizId, setQuizId] = useState('');
  const [preview, setPreview] = useState<Question[] | null>(null);
  const [summary, setSummary] = useState<{ imported: number; skipped: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handlePreviewAndImport(e: React.FormEvent) {
    e.preventDefault();
    if (!quizId.trim()) return;
    setError(null);
    setPreview(null);
    setSummary(null);
    try {
      const result = await importMutation.mutateAsync(quizId.trim());
      setPreview(result.questions);
      setSummary({ imported: result.imported, skipped: result.skipped });
    } catch (err) {
      setError(err instanceof Error ? err.message : t('app.error'));
    }
  }

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('questionBank.import.title')}</h1>
          <p className="page-subtitle">{t('questionBank.import.subtitle')}</p>
        </div>
        <button type="button" className="btn btn-secondary" onClick={() => navigate('/question-bank')}>
          {t('app.back')}
        </button>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <div className="card" style={{ maxWidth: 480, padding: 24, marginBottom: 24 }}>
        <form onSubmit={handlePreviewAndImport}>
          <div className="form-field">
            <label htmlFor="quizId">{t('questionBank.import.quizId')}</label>
            <input
              id="quizId"
              className="input"
              value={quizId}
              onChange={(e) => setQuizId(e.target.value)}
              placeholder={t('questionBank.import.quizIdPlaceholder')}
              required
              disabled={importMutation.isPending}
            />
            <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
              {t('questionBank.import.quizIdHint')}
            </span>
          </div>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={importMutation.isPending || !quizId.trim()}
          >
            {importMutation.isPending ? t('app.loading') : t('questionBank.import.submit')}
          </button>
        </form>
      </div>

      {summary && (
        <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
          <Badge variant="success">{t('questionBank.import.imported', { count: summary.imported })}</Badge>
          {summary.skipped > 0 && (
            <Badge variant="warning">{t('questionBank.import.skipped', { count: summary.skipped })}</Badge>
          )}
        </div>
      )}

      {preview && preview.length > 0 && (
        <>
          <h2 style={{ marginBottom: 12, fontSize: 16 }}>{t('questionBank.import.previewTitle')}</h2>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{t('questionBank.cols.text')}</th>
                  <th>{t('questionBank.cols.type')}</th>
                  <th>{t('questionBank.cols.difficulty')}</th>
                </tr>
              </thead>
              <tbody>
                {preview.map((q) => (
                  <tr key={q.id}>
                    <td style={{ maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{q.text}</td>
                    <td>
                      <Badge variant={TYPE_VARIANT[q.type]}>{t(`questionBank.types.${q.type}`)}</Badge>
                    </td>
                    <td>
                      <Badge variant={DIFFICULTY_VARIANT[q.difficulty]}>{t(`questionBank.difficulty.${q.difficulty}`)}</Badge>
                    </td>
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
