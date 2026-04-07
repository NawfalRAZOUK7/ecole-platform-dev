import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { EmptyState } from '@/shared/ui/EmptyState';
import type { Quiz } from './teacher.service';

export interface TeacherQuizListViewProps {
  hasNextPage: boolean;
  isFetchingNextPage: boolean;
  quizzes: Quiz[];
  onCreate: () => void;
  onFetchNextPage: () => void;
  onPublish: (quizId: string) => void;
}

export function TeacherQuizListView({
  hasNextPage,
  isFetchingNextPage,
  quizzes,
  onCreate,
  onFetchNextPage,
  onPublish,
}: TeacherQuizListViewProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <>
      <div className="filters-bar" style={{ marginBottom: 16 }}>
        <button className="btn btn-primary" onClick={onCreate}>
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
                    <td>{quiz.subject ? t(`cms.subjects.${quiz.subject}`, quiz.subject) : '-'}</td>
                    <td>{quiz.difficulty || '-'}</td>
                    <td>{quiz.question_count}</td>
                    <td>{quiz.total_points}</td>
                    <td><span className={`status-badge status-${quiz.status}`}>{quiz.status}</span></td>
                    <td>
                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        <button
                          className="btn btn-secondary"
                          style={{ fontSize: 12, padding: '4px 10px' }}
                          onClick={() => navigate(`/quizzes/${quiz.id}/analytics`)}
                        >
                          {t('teacherQuiz.analytics')}
                        </button>
                        {quiz.status === 'draft' && quiz.school_id ? (
                          <button
                            className="btn btn-primary"
                            style={{ fontSize: 12, padding: '4px 10px' }}
                            onClick={() => onPublish(quiz.id)}
                          >
                            {t('teacherQuiz.publish')}
                          </button>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {hasNextPage ? (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <button className="btn btn-secondary" onClick={onFetchNextPage} disabled={isFetchingNextPage}>
                {isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          ) : null}
        </>
      )}
    </>
  );
}
