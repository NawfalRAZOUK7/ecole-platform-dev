/**
 * Teacher Quiz Manager — create class-specific quizzes, assign platform quizzes.
 *
 * Phase 10B — Teacher creates school-scoped quizzes and assigns published
 * platform quizzes to assignments.
 * API: POST /quizzes, GET /quizzes, PUT /quizzes/{id}, POST /quizzes/{id}/publish
 */

import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { TeacherQuizCreateForm } from './TeacherQuizCreateForm';
import { TeacherQuizListView } from './TeacherQuizListView';
import { type QuizManagerView, type TeacherQuizPayload } from './teacher-quiz.types';
import { useCreateQuiz, usePublishQuiz, useTeacherQuizzes } from './useTeacher';
import type { Quiz } from './teacher.service';

export function QuizManagerPage() {
  const { t } = useTranslation();
  const [view, setView] = useState<QuizManagerView>('list');
  const quizzesQuery = useTeacherQuizzes();
  const createQuizMutation = useCreateQuiz();
  const publishQuizMutation = usePublishQuiz();
  const quizzes: Quiz[] = useMemo(() => quizzesQuery.data?.pages.flatMap((page) => page.data) ?? [], [quizzesQuery.data]);
  const dismissibleError = useDismissibleError(useMemo(() => toBannerError(quizzesQuery.error ?? createQuizMutation.error ?? publishQuizMutation.error, t('app.error')), [createQuizMutation.error, publishQuizMutation.error, quizzesQuery.error, t]));

  async function handlePublish(quizId: string) {
    await publishQuizMutation.mutateAsync(quizId);
    await quizzesQuery.refetch();
  }

  async function handleCreate(payload: TeacherQuizPayload) {
    await createQuizMutation.mutateAsync(payload);
    setView('list');
    await quizzesQuery.refetch();
  }

  if (quizzesQuery.isLoading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('teacherQuiz.title')}</h1>
      <ErrorBanner error={dismissibleError.error} onDismiss={dismissibleError.dismiss} onRetry={() => void quizzesQuery.refetch()} />

      {view === 'list' ? (
        <TeacherQuizListView
          hasNextPage={Boolean(quizzesQuery.hasNextPage)}
          isFetchingNextPage={quizzesQuery.isFetchingNextPage}
          quizzes={quizzes}
          onCreate={() => setView('create')}
          onFetchNextPage={() => void quizzesQuery.fetchNextPage()}
          onPublish={(quizId) => void handlePublish(quizId)}
        />
      ) : (
        <TeacherQuizCreateForm
          isSubmitting={createQuizMutation.isPending}
          onCancel={() => setView('list')}
          onCreate={handleCreate}
        />
      )}
    </div>
  );
}
