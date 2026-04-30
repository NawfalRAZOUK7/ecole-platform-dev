import { lazy } from 'react';

// Auth
export const LoginPage = lazy(() =>
  import('@/features/auth/LoginPage').then((m) => ({ default: m.LoginPage })),
);
export const RegisterPage = lazy(() =>
  import('@/features/auth/RegisterPage').then((m) => ({ default: m.RegisterPage })),
);
export const ForgotPasswordPage = lazy(() =>
  import('@/features/auth/ForgotPasswordPage').then((m) => ({ default: m.ForgotPasswordPage })),
);
export const ResetPasswordPage = lazy(() =>
  import('@/features/auth/ResetPasswordPage').then((m) => ({ default: m.ResetPasswordPage })),
);

// Admin
export const DashboardPage = lazy(() =>
  import('@/features/admin/DashboardPage').then((m) => ({ default: m.DashboardPage })),
);
export const UsersPage = lazy(() =>
  import('@/features/admin/UsersPage').then((m) => ({ default: m.UsersPage })),
);
export const InvitationsPage = lazy(() =>
  import('@/features/admin/InvitationsPage').then((m) => ({ default: m.InvitationsPage })),
);
export const AuditLogPage = lazy(() =>
  import('@/features/admin/AuditLogPage').then((m) => ({ default: m.AuditLogPage })),
);
export const SchoolSettingsPage = lazy(() =>
  import('@/features/admin/SchoolSettingsPage').then((m) => ({ default: m.SchoolSettingsPage })),
);
export const JustificationReviewPage = lazy(() =>
  import('@/features/admin/JustificationReviewPage').then((m) => ({
    default: m.JustificationReviewPage,
  })),
);
export const BatchRegisterPage = lazy(() =>
  import('@/features/admin/BatchRegisterPage').then((m) => ({ default: m.BatchRegisterPage })),
);
export const ParentChildLinksPage = lazy(() =>
  import('@/features/admin/ParentChildLinksPage').then((m) => ({
    default: m.ParentChildLinksPage,
  })),
);
export const BadgesPage = lazy(() =>
  import('@/features/admin/BadgesPage').then((m) => ({ default: m.BadgesPage })),
);
export const ProgramsPage = lazy(() =>
  import('@/features/admin/ProgramsPage').then((m) => ({ default: m.ProgramsPage })),
);
export const EnrollmentsPage = lazy(() =>
  import('@/features/admin/EnrollmentsPage').then((m) => ({ default: m.EnrollmentsPage })),
);
export const ProgramEquivalencesPage = lazy(() =>
  import('@/features/admin/ProgramEquivalencesPage').then((m) => ({
    default: m.ProgramEquivalencesPage,
  })),
);
export const ProgramVersionsPage = lazy(() =>
  import('@/features/admin/ProgramVersionsPage').then((m) => ({
    default: m.ProgramVersionsPage,
  })),
);
export const EligibilityRulesPage = lazy(() =>
  import('@/features/admin/EligibilityRulesPage').then((m) => ({
    default: m.EligibilityRulesPage,
  })),
);
export const StudentAcademicHistoryPage = lazy(() =>
  import('@/features/admin/StudentAcademicHistoryPage').then((m) => ({
    default: m.StudentAcademicHistoryPage,
  })),
);

// Analytics
export const AnalyticsDashboardPage = lazy(() =>
  import('@/features/analytics/AnalyticsDashboardPage').then((m) => ({
    default: m.AnalyticsDashboardPage,
  })),
);

// Teacher
export const TeacherClassesPage = lazy(() =>
  import('@/features/teacher/ClassesPage').then((m) => ({ default: m.ClassesPage })),
);
export const TeacherCoursesPage = lazy(() =>
  import('@/features/teacher/CoursesPage').then((m) => ({ default: m.CoursesPage })),
);
export const AssignmentFormPage = lazy(() =>
  import('@/features/teacher/AssignmentFormPage').then((m) => ({ default: m.AssignmentFormPage })),
);
export const TeacherSubmissionsPage = lazy(() =>
  import('@/features/teacher/SubmissionsPage').then((m) => ({ default: m.SubmissionsPage })),
);
export const TeacherAttendancePage = lazy(() =>
  import('@/features/teacher/AttendancePage').then((m) => ({ default: m.AttendancePage })),
);
export const AssessmentFormPage = lazy(() =>
  import('@/features/teacher/AssessmentFormPage').then((m) => ({ default: m.AssessmentFormPage })),
);
export const ContentLibraryPage = lazy(() =>
  import('@/features/teacher/ContentLibraryPage').then((m) => ({ default: m.ContentLibraryPage })),
);
export const QuizManagerPage = lazy(() =>
  import('@/features/teacher/QuizManagerPage').then((m) => ({ default: m.QuizManagerPage })),
);
export const ClassProgressPage = lazy(() =>
  import('@/features/teacher/ClassProgressPage').then((m) => ({ default: m.ClassProgressPage })),
);

// Student
export const StudentHomePage = lazy(() =>
  import('@/features/student/StudentHomePage').then((m) => ({ default: m.StudentHomePage })),
);
export const StudentContentPage = lazy(() =>
  import('@/features/student/StudentContentPage').then((m) => ({
    default: m.StudentContentPage,
  })),
);
export const ContentViewPage = lazy(() =>
  import('@/features/student/ContentViewPage').then((m) => ({ default: m.ContentViewPage })),
);
export const StoryViewerPage = lazy(() =>
  import('@/features/student/StoryViewerPage').then((m) => ({
    default: m.StoryViewerPage,
  })),
);
export const ColoringViewerPage = lazy(() =>
  import('@/features/student/ColoringViewerPage').then((m) => ({
    default: m.ColoringViewerPage,
  })),
);
export const QuizPlayerPage = lazy(() =>
  import('@/features/student/QuizPlayerPage').then((m) => ({ default: m.QuizPlayerPage })),
);
export const WritingWorkspacePage = lazy(() =>
  import('@/features/student/WritingWorkspacePage').then((m) => ({
    default: m.WritingWorkspacePage,
  })),
);

// Attendance
export const AttendanceModulePage = lazy(() =>
  import('@/features/attendance/AttendancePage').then((m) => ({ default: m.AttendancePage })),
);
export const AttendanceHistoryPage = lazy(() =>
  import('@/features/attendance/AttendanceHistoryPage').then((m) => ({
    default: m.AttendanceHistoryPage,
  })),
);
export const AttendanceAnalyticsPage = lazy(() =>
  import('@/features/attendance/AttendanceAnalyticsPage').then((m) => ({
    default: m.AttendanceAnalyticsPage,
  })),
);
export const ParentJustificationPage = lazy(() =>
  import('@/features/attendance/ParentJustificationPage').then((m) => ({
    default: m.ParentJustificationPage,
  })),
);

// Gradebook
export const GradebookPage = lazy(() =>
  import('@/features/gradebook/GradebookPage').then((m) => ({ default: m.GradebookPage })),
);
export const GradeDetailPage = lazy(() =>
  import('@/features/gradebook/GradeDetailPage').then((m) => ({ default: m.GradeDetailPage })),
);

// Budgets
export const BudgetListPage = lazy(() =>
  import('@/features/budgets/BudgetListPage').then((m) => ({ default: m.BudgetListPage })),
);
export const BudgetRequestPage = lazy(() =>
  import('@/features/budgets/BudgetRequestPage').then((m) => ({ default: m.BudgetRequestPage })),
);
export const BudgetAnalyticsPage = lazy(() =>
  import('@/features/budgets/BudgetAnalyticsPage').then((m) => ({
    default: m.BudgetAnalyticsPage,
  })),
);
export const BudgetDetailPage = lazy(() =>
  import('@/features/budgets/BudgetDetailPage').then((m) => ({ default: m.BudgetDetailPage })),
);

// Micro-schools
export const MicroSchoolListPage = lazy(() =>
  import('@/features/micro-schools/MicroSchoolListPage').then((m) => ({
    default: m.MicroSchoolListPage,
  })),
);
export const MicroSchoolDetailPage = lazy(() =>
  import('@/features/micro-schools/MicroSchoolDetailPage').then((m) => ({
    default: m.MicroSchoolDetailPage,
  })),
);
export const MicroSchoolEnrollPage = lazy(() =>
  import('@/features/micro-schools/MicroSchoolEnrollPage').then((m) => ({
    default: m.MicroSchoolEnrollPage,
  })),
);

// Timetable
export const TimetablePage = lazy(() =>
  import('@/features/timetable/TimetablePage').then((m) => ({ default: m.TimetablePage })),
);
export const TimetableConstraintsPage = lazy(() =>
  import('@/features/timetable/TimetableConstraintsPage').then((m) => ({
    default: m.TimetableConstraintsPage,
  })),
);
export const TimetableGeneratePage = lazy(() =>
  import('@/features/timetable/TimetableGeneratePage').then((m) => ({
    default: m.TimetableGeneratePage,
  })),
);

// Messages
export const ConversationsPage = lazy(() =>
  import('@/features/messages/ConversationsPage').then((m) => ({ default: m.ConversationsPage })),
);
export const ChatPage = lazy(() =>
  import('@/features/messages/ChatPage').then((m) => ({ default: m.ChatPage })),
);

// Family (parent overview)
export const MyChildrenPage = lazy(() =>
  import('@/features/family/MyChildrenPage').then((m) => ({
    default: m.MyChildrenPage,
  })),
);
export const SharedReviewPage = lazy(() =>
  import('@/features/family/SharedReviewPage').then((m) => ({
    default: m.SharedReviewPage,
  })),
);
export const ReviewDetailPage = lazy(() =>
  import('@/features/family/ReviewDetailPage').then((m) => ({
    default: m.ReviewDetailPage,
  })),
);

// Progress
export const ProgressDashboardPage = lazy(() =>
  import('@/features/progress/ProgressDashboardPage').then((m) => ({
    default: m.ProgressDashboardPage,
  })),
);
export const ParentProgressPage = lazy(() =>
  import('@/features/progress/ParentProgressPage').then((m) => ({
    default: m.ParentProgressPage,
  })),
);

// Announcements
export const AnnouncementsPage = lazy(() =>
  import('@/features/announcements/AnnouncementsPage').then((m) => ({
    default: m.AnnouncementsPage,
  })),
);

// Feed
export const FeedPage = lazy(() =>
  import('@/features/feed/FeedPage').then((m) => ({ default: m.FeedPage })),
);

// Rewards
export const RewardsPage = lazy(() =>
  import('@/features/rewards/RewardsPage').then((m) => ({ default: m.RewardsPage })),
);
export const StudentRewardsPage = lazy(() =>
  import('@/features/rewards/StudentRewardsPage').then((m) => ({
    default: m.StudentRewardsPage,
  })),
);
export const LeaderboardPage = lazy(() =>
  import('@/features/rewards/LeaderboardPage').then((m) => ({
    default: m.LeaderboardPage,
  })),
);

// Games
export const GamesListPage = lazy(() =>
  import('@/features/games/GamesListPage').then((m) => ({
    default: m.GamesListPage,
  })),
);
export const GameConfigDetailPage = lazy(() =>
  import('@/features/games/GameConfigDetailPage').then((m) => ({
    default: m.GameConfigDetailPage,
  })),
);
export const GameConfigEditor = lazy(() =>
  import('@/features/games/GameConfigEditor').then((m) => ({
    default: m.GameConfigEditor,
  })),
);
export const StudentGamesPage = lazy(() =>
  import('@/features/games/StudentGamesPage').then((m) => ({
    default: m.StudentGamesPage,
  })),
);
export const GamePlayerPage = lazy(() =>
  import('@/features/games/GamePlayerPage').then((m) => ({
    default: m.GamePlayerPage,
  })),
);

// Notifications
export const NotificationsPage = lazy(() =>
  import('@/features/notifications/NotificationsPage').then((m) => ({
    default: m.NotificationsPage,
  })),
);
export const NotificationSettingsPage = lazy(() =>
  import('@/features/notifications/NotificationSettingsPage').then((m) => ({
    default: m.NotificationSettingsPage,
  })),
);

// Calendar
export const CalendarPage = lazy(() =>
  import('@/features/calendar/CalendarPage').then((m) => ({ default: m.CalendarPage })),
);
export const EventDetailPage = lazy(() =>
  import('@/features/calendar/EventDetailPage').then((m) => ({ default: m.EventDetailPage })),
);
export const HolidayManagerPage = lazy(() =>
  import('@/features/calendar/HolidayManagerPage').then((m) => ({ default: m.HolidayManagerPage })),
);

// Reports
export const ReportsPage = lazy(() =>
  import('@/features/reports/ReportsPage').then((m) => ({ default: m.ReportsPage })),
);

// Documents
export const DocumentsPage = lazy(() =>
  import('@/features/documents/DocumentsPage').then((m) => ({ default: m.DocumentsPage })),
);
export const ResourcesPage = lazy(() =>
  import('@/features/documents/ResourcesPage').then((m) => ({ default: m.ResourcesPage })),
);
export const DocumentVersionsPage = lazy(() =>
  import('@/features/documents/DocumentVersionsPage').then((m) => ({
    default: m.DocumentVersionsPage,
  })),
);
export const DocumentPreviewPage = lazy(() =>
  import('@/features/documents/DocumentPreviewPage').then((m) => ({
    default: m.DocumentPreviewPage,
  })),
);
export const StudentDocumentsPage = lazy(() =>
  import('@/features/documents/StudentDocumentsPage').then((m) => ({
    default: m.StudentDocumentsPage,
  })),
);

// Content
export const ContentPage = lazy(() =>
  import('@/features/content/ContentPage').then((m) => ({ default: m.ContentPage })),
);
export const ContentDetailPage = lazy(() =>
  import('@/features/content/ContentDetailPage').then((m) => ({ default: m.ContentDetailPage })),
);
export const ContentPlayerPage = lazy(() =>
  import('@/features/content/ContentPlayerPage').then((m) => ({ default: m.ContentPlayerPage })),
);

// Results
export const ResultsPage = lazy(() =>
  import('@/features/results/ResultsPage').then((m) => ({ default: m.ResultsPage })),
);

// Invoices
export const InvoicesPage = lazy(() =>
  import('@/features/invoices/InvoicesPage').then((m) => ({ default: m.InvoicesPage })),
);
export const InvoiceDetailPage = lazy(() =>
  import('@/features/invoices/InvoiceDetailPage').then((m) => ({ default: m.InvoiceDetailPage })),
);

// Activities
export const ActivitiesPage = lazy(() =>
  import('@/features/activities/ActivitiesPage').then((m) => ({ default: m.ActivitiesPage })),
);
export const ActivityDetailPage = lazy(() =>
  import('@/features/activities/ActivityDetailPage').then((m) => ({
    default: m.ActivityDetailPage,
  })),
);

// Profile
export const ProfilePage = lazy(() =>
  import('@/features/profile/ProfilePage').then((m) => ({ default: m.ProfilePage })),
);
export const SessionsPage = lazy(() =>
  import('@/features/profile/SessionsPage').then((m) => ({ default: m.SessionsPage })),
);
export const TwoFactorPage = lazy(() =>
  import('@/features/profile/TwoFactorPage').then((m) => ({ default: m.TwoFactorPage })),
);
export const LoginHistoryPage = lazy(() =>
  import('@/features/profile/LoginHistoryPage').then((m) => ({ default: m.LoginHistoryPage })),
);

// Submissions
export const StudentSubmissionPage = lazy(() =>
  import('@/features/submissions/StudentSubmissionPage').then((m) => ({
    default: m.StudentSubmissionPage,
  })),
);

// Skills
export const SkillsOverviewPage = lazy(() =>
  import('@/features/skills/SkillsOverviewPage').then((m) => ({ default: m.SkillsOverviewPage })),
);
export const SkillPassportPage = lazy(() =>
  import('@/features/skills/SkillPassportPage').then((m) => ({ default: m.SkillPassportPage })),
);
export const SkillEvaluationPage = lazy(() =>
  import('@/features/skills/SkillEvaluationPage').then((m) => ({
    default: m.SkillEvaluationPage,
  })),
);
export const SkillAnalyticsPage = lazy(() =>
  import('@/features/skills/SkillAnalyticsPage').then((m) => ({ default: m.SkillAnalyticsPage })),
);

// Compliance
export const ComplianceDashboardPage = lazy(() =>
  import('@/features/compliance/ComplianceDashboardPage').then((m) => ({
    default: m.ComplianceDashboardPage,
  })),
);
export const CurriculumMappingPage = lazy(() =>
  import('@/features/compliance/CurriculumMappingPage').then((m) => ({
    default: m.CurriculumMappingPage,
  })),
);
export const ComplianceReportPage = lazy(() =>
  import('@/features/compliance/ComplianceReportPage').then((m) => ({
    default: m.ComplianceReportPage,
  })),
);

// Sync
export const SyncStatusPage = lazy(() =>
  import('@/features/sync/SyncStatusPage').then((m) => ({ default: m.SyncStatusPage })),
);
export const SyncConflictsPage = lazy(() =>
  import('@/features/sync/SyncConflictsPage').then((m) => ({ default: m.SyncConflictsPage })),
);
export const SyncSettingsPage = lazy(() =>
  import('@/features/sync/SyncSettingsPage').then((m) => ({ default: m.SyncSettingsPage })),
);

// Financial Health
export const FinancialDashboardPage = lazy(() =>
  import('@/features/financial-health/FinancialDashboardPage').then((m) => ({
    default: m.FinancialDashboardPage,
  })),
);
export const FinancialSnapshotsPage = lazy(() =>
  import('@/features/financial-health/FinancialSnapshotsPage').then((m) => ({
    default: m.FinancialSnapshotsPage,
  })),
);
export const FinancialExportPage = lazy(() =>
  import('@/features/financial-health/FinancialExportPage').then((m) => ({
    default: m.FinancialExportPage,
  })),
);

// Billing
export const FeeStructuresPage = lazy(() =>
  import('@/features/billing/FeeStructuresPage').then((m) => ({ default: m.FeeStructuresPage })),
);
export const FeeAssignmentsPage = lazy(() =>
  import('@/features/billing/FeeAssignmentsPage').then((m) => ({
    default: m.FeeAssignmentsPage,
  })),
);
export const GenerateInvoicesPage = lazy(() =>
  import('@/features/billing/GenerateInvoicesPage').then((m) => ({
    default: m.GenerateInvoicesPage,
  })),
);
export const SiblingPolicyPage = lazy(() =>
  import('@/features/billing/SiblingPolicyPage').then((m) => ({ default: m.SiblingPolicyPage })),
);
export const LateFeePolicyPage = lazy(() =>
  import('@/features/billing/LateFeePolicyPage').then((m) => ({ default: m.LateFeePolicyPage })),
);
export const PaymentPlansPage = lazy(() =>
  import('@/features/billing/PaymentPlansPage').then((m) => ({ default: m.PaymentPlansPage })),
);
export const PaymentPlanDetailPage = lazy(() =>
  import('@/features/billing/PaymentPlanDetailPage').then((m) => ({
    default: m.PaymentPlanDetailPage,
  })),
);

// Rubrics
export const RubricsListPage = lazy(() =>
  import('@/features/rubrics/RubricsListPage').then((m) => ({ default: m.RubricsListPage })),
);
export const RubricEditorPage = lazy(() =>
  import('@/features/rubrics/RubricEditorPage').then((m) => ({ default: m.RubricEditorPage })),
);
export const RubricGradingPage = lazy(() =>
  import('@/features/rubrics/RubricGradingPage').then((m) => ({ default: m.RubricGradingPage })),
);

// Question Bank
export const QuestionBankPage = lazy(() =>
  import('@/features/question-bank/QuestionBankPage').then((m) => ({
    default: m.QuestionBankPage,
  })),
);
export const QuestionBankImportPage = lazy(() =>
  import('@/features/question-bank/QuestionBankImportPage').then((m) => ({
    default: m.QuestionBankImportPage,
  })),
);
export const GenerateQuizPage = lazy(() =>
  import('@/features/question-bank/GenerateQuizPage').then((m) => ({
    default: m.GenerateQuizPage,
  })),
);

// CMS
export const CmsContentListPage = lazy(() =>
  import('@/features/cms/ContentListPage').then((m) => ({ default: m.CmsContentListPage })),
);
export const CmsContentUploadPage = lazy(() =>
  import('@/features/cms/ContentUploadPage').then((m) => ({ default: m.CmsContentUploadPage })),
);
export const CmsContentEditPage = lazy(() =>
  import('@/features/cms/ContentEditPage').then((m) => ({ default: m.CmsContentEditPage })),
);
export const CmsReviewQueuePage = lazy(() =>
  import('@/features/cms/ReviewQueuePage').then((m) => ({ default: m.CmsReviewQueuePage })),
);
export const CmsQuizBuilderPage = lazy(() =>
  import('@/features/cms/QuizBuilderPage').then((m) => ({ default: m.CmsQuizBuilderPage })),
);
export const CmsAnalyticsPage = lazy(() =>
  import('@/features/cms/AnalyticsPage').then((m) => ({ default: m.CmsAnalyticsPage })),
);
