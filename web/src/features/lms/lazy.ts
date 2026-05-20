import { lazy } from 'react';

export const TeacherCoursesPage = lazy(() =>
  import('./teacher/ui/CoursesPage').then((m) => ({ default: m.CoursesPage })),
);
export const AssignmentFormPage = lazy(() =>
  import('./teacher/ui/AssignmentFormPage').then((m) => ({ default: m.AssignmentFormPage })),
);
export const TeacherSubmissionsPage = lazy(() =>
  import('./teacher/ui/SubmissionsPage').then((m) => ({ default: m.SubmissionsPage })),
);
export const AssessmentFormPage = lazy(() =>
  import('./teacher/ui/AssessmentFormPage').then((m) => ({ default: m.AssessmentFormPage })),
);
export const QuizManagerPage = lazy(() =>
  import('./teacher/ui/QuizManagerPage').then((m) => ({ default: m.QuizManagerPage })),
);

export const QuizPlayerPage = lazy(() =>
  import('./student/ui/QuizPlayerPage').then((m) => ({ default: m.QuizPlayerPage })),
);
export const WritingWorkspacePage = lazy(() =>
  import('./student/ui/WritingWorkspacePage').then((m) => ({ default: m.WritingWorkspacePage })),
);
export const StudentSubmissionPage = lazy(() =>
  import('./submissions/ui/StudentSubmissionPage').then((m) => ({
    default: m.StudentSubmissionPage,
  })),
);

export const RubricsListPage = lazy(() =>
  import('./rubrics/ui/RubricsListPage').then((m) => ({ default: m.RubricsListPage })),
);
export const RubricEditorPage = lazy(() =>
  import('./rubrics/ui/RubricEditorPage').then((m) => ({ default: m.RubricEditorPage })),
);
export const RubricGradingPage = lazy(() =>
  import('./rubrics/ui/RubricGradingPage').then((m) => ({ default: m.RubricGradingPage })),
);

export const QuestionBankPage = lazy(() =>
  import('./question-bank/ui/QuestionBankPage').then((m) => ({ default: m.QuestionBankPage })),
);
export const QuestionBankImportPage = lazy(() =>
  import('./question-bank/ui/QuestionBankImportPage').then((m) => ({
    default: m.QuestionBankImportPage,
  })),
);
export const GenerateQuizPage = lazy(() =>
  import('./question-bank/ui/GenerateQuizPage').then((m) => ({ default: m.GenerateQuizPage })),
);
