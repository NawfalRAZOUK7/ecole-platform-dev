/**
 * CMS Quiz Builder — create/edit quizzes with all 5 question types.
 *
 * Phase 10A — MCQ, True/False, Fill-in, Drag&Drop, Matching editors.
 * Question reorder, preview mode, quiz metadata form.
 */

import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { LoadingState } from '@/shared/ui/LoadingState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { QuestionList } from './QuestionList';
import { QuizBuilderForm } from './QuizBuilderForm';
import { QuizListView } from './QuizListView';
import { QuizPreview } from './QuizPreview';
import { defaultQuestion, nextKey, type Question, type QuestionType } from './quiz-builder.types';
import { useCmsQuiz, useCreateCmsQuiz, usePublishCmsQuiz, useUpdateCmsQuiz } from './useCms';

export function CmsQuizBuilderPage() {
  const { quizId } = useParams<{ quizId: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const isEdit = Boolean(quizId);
  const quizQuery = useCmsQuiz(quizId);
  const createQuizMutation = useCreateCmsQuiz();
  const updateQuizMutation = useUpdateCmsQuiz();
  const publishQuizMutation = usePublishCmsQuiz();

  const [showBuilder, setShowBuilder] = useState(isEdit);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [quizSubject, setQuizSubject] = useState('');
  const [levelBand, setLevelBand] = useState('');
  const [difficulty, setDifficulty] = useState('MEDIUM');
  const [timeLimit, setTimeLimit] = useState<number | ''>('');
  const [maxAttempts, setMaxAttempts] = useState(1);
  const [shuffle, setShuffle] = useState(false);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [previewMode, setPreviewMode] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!quizQuery.data) return;
    const quiz = quizQuery.data;
    setTitle(quiz.title);
    setDescription(quiz.description || '');
    setQuizSubject(quiz.subject || '');
    setLevelBand(quiz.level_band || '');
    setDifficulty(quiz.difficulty || 'MEDIUM');
    setTimeLimit(quiz.time_limit_minutes ?? '');
    setMaxAttempts(quiz.max_attempts);
    setShuffle(quiz.shuffle_questions);
    setQuestions((quiz.questions ?? []).map((question, index) => ({ _key: nextKey(), question_type: question.question_type as QuestionType, question_text: question.question_text, options: question.options, correct_answer: question.correct_answer, points: question.points, order: index, explanation: question.explanation || '' })));
    setShowBuilder(true);
  }, [quizQuery.data]);

  function updateQuestion(index: number, updatedQuestion: Question) {
    setQuestions((current) => current.map((question, questionIndex) => (questionIndex === index ? updatedQuestion : question)));
  }

  function removeQuestion(index: number) {
    setQuestions((current) => current.filter((_, questionIndex) => questionIndex !== index).map((question, questionIndex) => ({ ...question, order: questionIndex })));
  }

  function moveQuestion(index: number, direction: -1 | 1) {
    setQuestions((current) => {
      const nextQuestions = [...current];
      const target = index + direction;
      if (target < 0 || target >= nextQuestions.length) return nextQuestions;
      [nextQuestions[index], nextQuestions[target]] = [nextQuestions[target], nextQuestions[index]];
      return nextQuestions.map((question, questionIndex) => ({ ...question, order: questionIndex }));
    });
  }

  async function handleSave(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSaved(false);

    const payload = {
      title,
      description: description || undefined,
      subject: quizSubject || undefined,
      level_band: levelBand || undefined,
      difficulty: difficulty || undefined,
      time_limit_minutes: timeLimit || undefined,
      max_attempts: maxAttempts,
      shuffle_questions: shuffle,
      questions: questions.map((question, index) => ({
        question_type: question.question_type,
        question_text: question.question_text,
        options: question.options,
        correct_answer: question.correct_answer,
        points: question.points,
        order: index,
        explanation: question.explanation || undefined,
      })),
    };

    try {
      if (isEdit) {
        await updateQuizMutation.mutateAsync({ quizId: quizId!, payload });
      } else {
        const createdQuiz = await createQuizMutation.mutateAsync(payload);
        navigate(`/cms/quizzes/${createdQuiz.id}/edit`, { replace: true });
      }
      setSaved(true);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : t('app.error'));
    }
  }

  async function handlePublish() {
    if (!quizId) return;
    try {
      await publishQuizMutation.mutateAsync(quizId);
      navigate('/cms/quizzes');
    } catch (publishError) {
      setError(publishError instanceof Error ? publishError.message : t('app.error'));
    }
  }

  const saving = createQuizMutation.isPending || updateQuizMutation.isPending;
  if (!showBuilder) {
    return <QuizListView onCreate={() => { setShowBuilder(true); setTitle(''); setQuestions([]); }} onEdit={(id) => navigate(`/cms/quizzes/${id}/edit`)} />;
  }
  if (isEdit && quizQuery.isLoading) return <LoadingState />;
  if (previewMode) return <QuizPreview questions={questions} onClose={() => setPreviewMode(false)} />;

  return (
    <div className="page">
      <QuizBuilderForm
        description={description}
        difficulty={difficulty}
        isEdit={isEdit}
        levelBand={levelBand}
        maxAttempts={maxAttempts}
        previewEnabled={questions.length > 0}
        questionCount={questions.length}
        quizSubject={quizSubject}
        saving={saving}
        shuffle={shuffle}
        timeLimit={timeLimit}
        title={title}
        onAddQuestion={(type) => setQuestions((current) => [...current, defaultQuestion(type, current.length)])}
        onBack={() => { setShowBuilder(false); navigate('/cms/quizzes'); }}
        onChangeDescription={setDescription}
        onChangeDifficulty={setDifficulty}
        onChangeLevelBand={setLevelBand}
        onChangeMaxAttempts={setMaxAttempts}
        onChangeQuizSubject={setQuizSubject}
        onChangeShuffle={setShuffle}
        onChangeTimeLimit={setTimeLimit}
        onChangeTitle={setTitle}
        onPreview={() => setPreviewMode(true)}
      />

      <ErrorBanner error={error || (quizQuery.error instanceof Error ? quizQuery.error.message : null)} onDismiss={() => setError(null)} />
      {saved && <div className="alert alert-success" style={{ marginBottom: 16, padding: 12, borderRadius: 8 }}>{t('cms.quiz.saved')}</div>}

      <form onSubmit={handleSave}>
        <QuestionList questions={questions} onChangeQuestion={updateQuestion} onMoveQuestion={moveQuestion} onRemoveQuestion={removeQuestion} />
        <div style={{ display: 'flex', gap: 12 }}>
          <button type="submit" className="btn btn-primary" disabled={saving || !title}>{saving ? t('app.loading') : t('app.save')}</button>
          {isEdit && <button type="button" className="btn btn-primary" onClick={() => void handlePublish()}>{t('cms.quiz.publish')}</button>}
        </div>
      </form>
    </div>
  );
}
