import { lazy } from 'react';

export const ProgramsPage = lazy(() =>
  import('./programs/ui/ProgramsPage').then((m) => ({ default: m.ProgramsPage })),
);
export const EnrollmentsPage = lazy(() =>
  import('./programs/ui/EnrollmentsPage').then((m) => ({ default: m.EnrollmentsPage })),
);
export const ProgramEquivalencesPage = lazy(() =>
  import('./programs/ui/ProgramEquivalencesPage').then((m) => ({
    default: m.ProgramEquivalencesPage,
  })),
);
export const ProgramVersionsPage = lazy(() =>
  import('./programs/ui/ProgramVersionsPage').then((m) => ({ default: m.ProgramVersionsPage })),
);
export const EligibilityRulesPage = lazy(() =>
  import('./programs/ui/EligibilityRulesPage').then((m) => ({ default: m.EligibilityRulesPage })),
);
export const StudentAcademicHistoryPage = lazy(() =>
  import('./programs/ui/StudentAcademicHistoryPage').then((m) => ({
    default: m.StudentAcademicHistoryPage,
  })),
);

export const AttendanceModulePage = lazy(() =>
  import('./attendance/ui/AttendancePage').then((m) => ({ default: m.AttendancePage })),
);
export const AttendanceHistoryPage = lazy(() =>
  import('./attendance/ui/AttendanceHistoryPage').then((m) => ({
    default: m.AttendanceHistoryPage,
  })),
);
export const AttendanceAnalyticsPage = lazy(() =>
  import('./attendance/ui/AttendanceAnalyticsPage').then((m) => ({
    default: m.AttendanceAnalyticsPage,
  })),
);
export const ParentJustificationPage = lazy(() =>
  import('./attendance/ui/ParentJustificationPage').then((m) => ({
    default: m.ParentJustificationPage,
  })),
);

export const GradebookPage = lazy(() =>
  import('./gradebook/ui/GradebookPage').then((m) => ({ default: m.GradebookPage })),
);
export const GradeDetailPage = lazy(() =>
  import('./gradebook/ui/GradeDetailPage').then((m) => ({ default: m.GradeDetailPage })),
);

export const TimetablePage = lazy(() =>
  import('./timetable/ui/TimetablePage').then((m) => ({ default: m.TimetablePage })),
);
export const TimetableConstraintsPage = lazy(() =>
  import('./timetable/ui/TimetableConstraintsPage').then((m) => ({
    default: m.TimetableConstraintsPage,
  })),
);
export const TimetableGeneratePage = lazy(() =>
  import('./timetable/ui/TimetableGeneratePage').then((m) => ({
    default: m.TimetableGeneratePage,
  })),
);

export const ProgressDashboardPage = lazy(() =>
  import('./progress/ui/ProgressDashboardPage').then((m) => ({ default: m.ProgressDashboardPage })),
);
export const ParentProgressPage = lazy(() =>
  import('./progress/ui/ParentProgressPage').then((m) => ({ default: m.ParentProgressPage })),
);

export const ResultsPage = lazy(() =>
  import('./results/ui/ResultsPage').then((m) => ({ default: m.ResultsPage })),
);

export const SkillsOverviewPage = lazy(() =>
  import('./skills/ui/SkillsOverviewPage').then((m) => ({ default: m.SkillsOverviewPage })),
);
export const SkillPassportPage = lazy(() =>
  import('./skills/ui/SkillPassportPage').then((m) => ({ default: m.SkillPassportPage })),
);
export const SkillEvaluationPage = lazy(() =>
  import('./skills/ui/SkillEvaluationPage').then((m) => ({ default: m.SkillEvaluationPage })),
);
export const SkillAnalyticsPage = lazy(() =>
  import('./skills/ui/SkillAnalyticsPage').then((m) => ({ default: m.SkillAnalyticsPage })),
);

export const TeacherClassesPage = lazy(() =>
  import('./teacher/ui/ClassesPage').then((m) => ({ default: m.ClassesPage })),
);
export const TeacherAttendancePage = lazy(() =>
  import('./teacher/ui/AttendancePage').then((m) => ({ default: m.AttendancePage })),
);
export const ClassProgressPage = lazy(() =>
  import('./teacher/ui/ClassProgressPage').then((m) => ({ default: m.ClassProgressPage })),
);
