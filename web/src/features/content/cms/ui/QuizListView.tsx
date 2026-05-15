import { useTranslation } from 'react-i18next';
import { LoadingState } from '@/shared/ui/LoadingState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { useCmsQuizzes } from '../model/useCms';

interface QuizListViewProps {
  onCreate: () => void;
  onEdit: (id: string) => void;
}

export function QuizListView({ onCreate, onEdit }: QuizListViewProps) {
  const { t } = useTranslation();
  const quizzesQuery = useCmsQuizzes();
  const quizzes = quizzesQuery.data ?? [];

  if (quizzesQuery.isLoading) return <LoadingState />;

  return (
    <div className="page">
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <h1 className="page-title">{t('cms.quiz.title')}</h1>
        <button className="btn btn-primary" onClick={onCreate}>
          {t('cms.quiz.create')}
        </button>
      </div>
      <ErrorBanner
        error={quizzesQuery.error instanceof Error ? quizzesQuery.error.message : null}
        onDismiss={() => {}}
        onRetry={() => void quizzesQuery.refetch()}
      />

      {quizzes.length === 0 ? (
        <p className="empty-state">{t('cms.quiz.empty')}</p>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
            gap: 16,
          }}
        >
          {quizzes.map((quiz) => (
            <div
              key={quiz.id}
              className="card"
              style={{ padding: 16, cursor: 'pointer' }}
              onClick={() => onEdit(quiz.id)}
            >
              <h3 style={{ margin: '0 0 4px', fontSize: 15 }}>{quiz.title}</h3>
              {quiz.description && (
                <p
                  style={{ margin: '0 0 8px', fontSize: 13, color: 'var(--color-text-secondary)' }}
                >
                  {quiz.description}
                </p>
              )}
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', fontSize: 11 }}>
                <span className={`badge badge--${quiz.status}`}>{quiz.status}</span>
                {quiz.subject && <span className="badge">{quiz.subject}</span>}
                {quiz.level_band && <span className="badge">{quiz.level_band}</span>}
                {quiz.difficulty && <span className="badge">{quiz.difficulty}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
