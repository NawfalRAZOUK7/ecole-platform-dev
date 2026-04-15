/**
 * École Platform — Application Root with Routing
 *
 * Reference: S-080 — Route guards, S-079 — Login, S-081 — Feature pages
 * Feature-first architecture per Pack E1.
 * Role-based redirect on root /.
 */

import { Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '@/services/auth/AuthContext';
import { ErrorBoundary } from '@/shared/ui/ErrorBoundary';
import { Layout } from '@/shared/ui/Layout';
import { OfflineIndicator } from '@/shared/ui/OfflineIndicator';
import { ROLE_REDIRECT } from '@/features/auth/LoginPage';
import { ProtectedRoute } from '@/features/auth/ProtectedRoute';
import { FeatureTogglesPage } from '@/features/admin/FeatureTogglesPage';
import { CmsLayout } from '@/features/cms/CmsLayout';
import { QuizAnalyticsPage } from '@/features/quizzes/QuizAnalyticsPage';
import { QuizResultsPage } from '@/features/quizzes/QuizResultsPage';
import { GDPRPage } from '@/features/settings/GDPRPage';
import { LoadingState } from '@/shared/ui/LoadingState';

import {
  LoginPage,
  RegisterPage,
  DashboardPage,
  UsersPage,
  InvitationsPage,
  AuditLogPage,
  SchoolSettingsPage,
  JustificationReviewPage,
  BatchRegisterPage,
  ParentChildLinksPage,
  AnalyticsDashboardPage,
  TeacherClassesPage,
  TeacherCoursesPage,
  AssignmentFormPage,
  TeacherSubmissionsPage,
  TeacherAttendancePage,
  AssessmentFormPage,
  ContentLibraryPage,
  QuizManagerPage,
  ClassProgressPage,
  ContentViewPage,
  QuizPlayerPage,
  AttendanceModulePage,
  AttendanceHistoryPage,
  AttendanceAnalyticsPage,
  ParentJustificationPage,
  GradebookPage,
  GradeDetailPage,
  BudgetListPage,
  BudgetRequestPage,
  BudgetAnalyticsPage,
  BudgetDetailPage,
  MicroSchoolListPage,
  MicroSchoolDetailPage,
  MicroSchoolEnrollPage,
  TimetablePage,
  ConversationsPage,
  ChatPage,
  ProgressDashboardPage,
  ParentProgressPage,
  AnnouncementsPage,
  FeedPage,
  RewardsPage,
  GamesListPage,
  GameConfigDetailPage,
  GameConfigEditor,
  NotificationsPage,
  NotificationSettingsPage,
  CalendarPage,
  EventDetailPage,
  HolidayManagerPage,
  ReportsPage,
  DocumentsPage,
  ResourcesPage,
  DocumentVersionsPage,
  DocumentPreviewPage,
  StudentDocumentsPage,
  ContentPage,
  ContentDetailPage,
  ContentPlayerPage,
  ResultsPage,
  InvoicesPage,
  InvoiceDetailPage,
  ActivitiesPage,
  ActivityDetailPage,
  ProfilePage,
  SessionsPage,
  TwoFactorPage,
  LoginHistoryPage,
  ForgotPasswordPage,
  ResetPasswordPage,
  StudentSubmissionPage,
  SkillsOverviewPage,
  SkillPassportPage,
  SkillEvaluationPage,
  SkillAnalyticsPage,
  ComplianceDashboardPage,
  CurriculumMappingPage,
  ComplianceReportPage,
  SyncStatusPage,
  SyncConflictsPage,
  SyncSettingsPage,
  FinancialDashboardPage,
  FinancialSnapshotsPage,
  FinancialExportPage,
  FeeStructuresPage,
  FeeAssignmentsPage,
  GenerateInvoicesPage,
  SiblingPolicyPage,
  LateFeePolicyPage,
  PaymentPlansPage,
  PaymentPlanDetailPage,
  CmsContentListPage,
  CmsContentUploadPage,
  CmsContentEditPage,
  CmsReviewQueuePage,
  CmsQuizBuilderPage,
  CmsAnalyticsPage,
  QuestionBankPage,
  QuestionBankImportPage,
  GenerateQuizPage,
  RubricsListPage,
  RubricEditorPage,
  RubricGradingPage,
  TimetableConstraintsPage,
  TimetableGeneratePage,
} from './LazyPages';

/** Redirect based on user role */
function RoleRedirect() {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) return <LoadingState />;

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  const target = ROLE_REDIRECT[user?.role || ''] || '/profile';
  return <Navigate to={target} replace />;
}

function App() {
  return (
    <div className="app-root">
      <OfflineIndicator />
      <ErrorBoundary onError={(error) => console.error(error)}>
        <Suspense fallback={<LoadingState />}>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />

            {/* Protected routes with layout */}
            <Route
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              {/* Admin routes (ADM, DIR) */}
              <Route
                path="/admin"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR']}>
                    <DashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/users"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR']}>
                    <UsersPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/invitations"
                element={
                  <ProtectedRoute roles={['ADM']}>
                    <InvitationsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/audit"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR']}>
                    <AuditLogPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/settings"
                element={
                  <ProtectedRoute roles={['ADM']}>
                    <SchoolSettingsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/school"
                element={
                  <ProtectedRoute roles={['ADM']}>
                    <SchoolSettingsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/features"
                element={
                  <ProtectedRoute roles={['SYS', 'ADM']}>
                    <FeatureTogglesPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/justifications"
                element={
                  <ProtectedRoute roles={['ADM']}>
                    <JustificationReviewPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/analytics"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR']}>
                    <AnalyticsDashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/analytics"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR']}>
                    <AnalyticsDashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/batch-register"
                element={
                  <ProtectedRoute roles={['ADM']}>
                    <BatchRegisterPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/family-links"
                element={
                  <ProtectedRoute roles={['ADM']}>
                    <ParentChildLinksPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/fee-structures"
                element={
                  <ProtectedRoute roles={['ADM']}>
                    <FeeStructuresPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/fee-assignments"
                element={
                  <ProtectedRoute roles={['ADM']}>
                    <FeeAssignmentsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/generate-invoices"
                element={
                  <ProtectedRoute roles={['ADM']}>
                    <GenerateInvoicesPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/billing/sibling-policy"
                element={
                  <ProtectedRoute roles={['ADM']}>
                    <SiblingPolicyPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/billing/late-fees"
                element={
                  <ProtectedRoute roles={['ADM']}>
                    <LateFeePolicyPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/billing/payment-plans/:planId"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR', 'PAR']}>
                    <PaymentPlanDetailPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/billing/payment-plans"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR', 'PAR']}>
                    <PaymentPlansPage />
                  </ProtectedRoute>
                }
              />

              {/* Teacher routes (TCH) */}
              <Route
                path="/teacher"
                element={
                  <ProtectedRoute roles={['TCH']}>
                    <TeacherClassesPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/courses"
                element={
                  <ProtectedRoute roles={['TCH']}>
                    <TeacherCoursesPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/assignments"
                element={
                  <ProtectedRoute roles={['TCH']}>
                    <AssignmentFormPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/submissions"
                element={
                  <ProtectedRoute roles={['TCH']}>
                    <TeacherSubmissionsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/attendance"
                element={
                  <ProtectedRoute roles={['TCH']}>
                    <TeacherAttendancePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/assessments"
                element={
                  <ProtectedRoute roles={['TCH']}>
                    <AssessmentFormPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/content-library"
                element={
                  <ProtectedRoute roles={['TCH']}>
                    <ContentLibraryPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/quizzes"
                element={
                  <ProtectedRoute roles={['TCH']}>
                    <QuizManagerPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/quizzes/:id/analytics"
                element={
                  <ProtectedRoute roles={['TCH']}>
                    <QuizAnalyticsPage />
                  </ProtectedRoute>
                }
              />

              {/* Student routes */}
              <Route
                path="/student/content"
                element={
                  <ProtectedRoute roles={['STD']}>
                    <ContentViewPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/student/quizzes"
                element={
                  <ProtectedRoute roles={['STD']}>
                    <QuizPlayerPage />
                  </ProtectedRoute>
                }
              />

              {/* Attendance */}
              <Route
                path="/attendance"
                element={
                  <ProtectedRoute roles={['TCH', 'DIR', 'ADM']}>
                    <AttendanceModulePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/attendance/history"
                element={
                  <ProtectedRoute roles={['STD', 'PAR']}>
                    <AttendanceHistoryPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/attendance/analytics"
                element={
                  <ProtectedRoute roles={['DIR', 'ADM']}>
                    <AttendanceAnalyticsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/attendance/justify"
                element={
                  <ProtectedRoute roles={['PAR']}>
                    <ParentJustificationPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/gradebook"
                element={
                  <ProtectedRoute roles={['TCH', 'DIR']}>
                    <GradebookPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/gradebook/student/:studentId"
                element={
                  <ProtectedRoute roles={['STD', 'PAR', 'TCH', 'DIR']}>
                    <GradeDetailPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/budgets"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR']}>
                    <BudgetListPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/budgets/requests"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR']}>
                    <BudgetRequestPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/budgets/analytics"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR']}>
                    <BudgetAnalyticsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/budgets/:id"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR']}>
                    <BudgetDetailPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/micro-schools"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR', 'PAR']}>
                    <MicroSchoolListPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/micro-schools/:id"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR', 'PAR']}>
                    <MicroSchoolDetailPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/micro-schools/:id/enroll"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR', 'PAR']}>
                    <MicroSchoolEnrollPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/timetable"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR', 'TCH', 'STD', 'PAR']}>
                    <TimetablePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/timetable/constraints"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR']}>
                    <TimetableConstraintsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/timetable/generate"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR']}>
                    <TimetableGeneratePage />
                  </ProtectedRoute>
                }
              />

              {/* Messaging (PAR, TCH, ADM, DIR) */}
              <Route
                path="/messages"
                element={
                  <ProtectedRoute roles={['PAR', 'TCH', 'ADM', 'DIR']}>
                    <ConversationsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/messages/:conversationId"
                element={
                  <ProtectedRoute roles={['PAR', 'TCH', 'ADM', 'DIR']}>
                    <ChatPage />
                  </ProtectedRoute>
                }
              />

              {/* Progress (Phase 12C) */}
              <Route
                path="/progress"
                element={
                  <ProtectedRoute roles={['STD', 'PAR']}>
                    <ProgressDashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/parent/progress"
                element={
                  <ProtectedRoute roles={['PAR']}>
                    <ParentProgressPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/class-progress"
                element={
                  <ProtectedRoute roles={['TCH']}>
                    <ClassProgressPage />
                  </ProtectedRoute>
                }
              />

              {/* Announcements (all roles) */}
              <Route
                path="/announcements"
                element={
                  <ProtectedRoute roles={['PAR', 'TCH', 'ADM', 'DIR', 'STD']}>
                    <AnnouncementsPage />
                  </ProtectedRoute>
                }
              />

              {/* Feature routes */}
              <Route
                path="/feed"
                element={
                  <ProtectedRoute roles={['PAR']}>
                    <FeedPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/rewards"
                element={
                  <ProtectedRoute roles={['STD', 'PAR', 'TCH', 'ADM', 'DIR', 'SUP', 'SYS']}>
                    <RewardsPage />
                  </ProtectedRoute>
                }
              />
              <Route path="/games" element={<Navigate to="/teacher/games" replace />} />
              <Route
                path="/teacher/games"
                element={
                  <ProtectedRoute roles={['TCH', 'ADM']}>
                    <GamesListPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/games/new"
                element={
                  <ProtectedRoute roles={['TCH', 'ADM']}>
                    <GameConfigEditor />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teacher/games/:id"
                element={
                  <ProtectedRoute roles={['TCH', 'ADM']}>
                    <GameConfigDetailPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/notifications"
                element={
                  <ProtectedRoute roles={['PAR', 'TCH', 'ADM', 'DIR', 'STD']}>
                    <NotificationsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/calendar"
                element={
                  <ProtectedRoute roles={['PAR', 'TCH', 'ADM', 'DIR', 'STD']}>
                    <CalendarPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/events/:id"
                element={
                  <ProtectedRoute roles={['PAR', 'TCH', 'ADM', 'DIR', 'STD']}>
                    <EventDetailPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/calendar/holidays"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR']}>
                    <HolidayManagerPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/reports"
                element={
                  <ProtectedRoute roles={['PAR', 'TCH', 'ADM', 'DIR', 'STD']}>
                    <ReportsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/documents"
                element={
                  <ProtectedRoute roles={['PAR', 'TCH', 'ADM', 'DIR', 'STD']}>
                    <DocumentsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/resources"
                element={
                  <ProtectedRoute roles={['PAR', 'TCH', 'ADM', 'DIR', 'STD']}>
                    <ResourcesPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/documents/:docId/versions"
                element={
                  <ProtectedRoute roles={['PAR', 'TCH', 'ADM', 'DIR', 'STD']}>
                    <DocumentVersionsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/documents/:docId/preview"
                element={
                  <ProtectedRoute roles={['PAR', 'TCH', 'ADM', 'DIR', 'STD']}>
                    <DocumentPreviewPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/students/:studentId/documents"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR', 'TCH', 'PAR', 'STD']}>
                    <StudentDocumentsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/settings/notifications"
                element={
                  <ProtectedRoute roles={['PAR', 'TCH', 'ADM', 'DIR', 'STD']}>
                    <NotificationSettingsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/settings/privacy"
                element={
                  <ProtectedRoute>
                    <GDPRPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/content"
                element={
                  <ProtectedRoute roles={['STD', 'PAR', 'TCH', 'ADM']}>
                    <ContentPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/content/:id"
                element={
                  <ProtectedRoute roles={['STD', 'PAR', 'TCH', 'ADM']}>
                    <ContentDetailPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/content/:id/play"
                element={
                  <ProtectedRoute roles={['STD', 'PAR', 'TCH', 'ADM']}>
                    <ContentPlayerPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/results"
                element={
                  <ProtectedRoute roles={['STD', 'PAR']}>
                    <ResultsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/quizzes/attempts/:id/results"
                element={
                  <ProtectedRoute roles={['STD', 'PAR', 'TCH', 'ADM', 'DIR']}>
                    <QuizResultsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/invoices"
                element={
                  <ProtectedRoute roles={['PAR', 'ADM']}>
                    <InvoicesPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/invoices/:id"
                element={
                  <ProtectedRoute roles={['PAR', 'ADM', 'DIR']}>
                    <InvoiceDetailPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/activities"
                element={
                  <ProtectedRoute roles={['STD', 'TCH', 'ADM']}>
                    <ActivitiesPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/activities/:id"
                element={
                  <ProtectedRoute roles={['STD', 'TCH', 'ADM']}>
                    <ActivityDetailPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/skills"
                element={
                  <ProtectedRoute roles={['TCH', 'DIR', 'PAR', 'STD']}>
                    <SkillsOverviewPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/skills/passport/:studentId"
                element={
                  <ProtectedRoute roles={['TCH', 'DIR', 'PAR', 'STD']}>
                    <SkillPassportPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/skills/evaluate"
                element={
                  <ProtectedRoute roles={['TCH', 'DIR']}>
                    <SkillEvaluationPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/skills/analytics"
                element={
                  <ProtectedRoute roles={['TCH', 'DIR']}>
                    <SkillAnalyticsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/compliance"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR']}>
                    <ComplianceDashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/compliance/mapping"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR']}>
                    <CurriculumMappingPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/compliance/reports"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR']}>
                    <ComplianceReportPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/sync"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR']}>
                    <SyncStatusPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/financial-health"
                element={
                  <ProtectedRoute roles={['ADM', 'SYS']}>
                    <FinancialDashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/financial-health/snapshots"
                element={
                  <ProtectedRoute roles={['ADM', 'SYS']}>
                    <FinancialSnapshotsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/financial-health/export"
                element={
                  <ProtectedRoute roles={['ADM', 'SYS']}>
                    <FinancialExportPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/sync/conflicts"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR']}>
                    <SyncConflictsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/sync/settings"
                element={
                  <ProtectedRoute roles={['ADM', 'DIR']}>
                    <SyncSettingsPage />
                  </ProtectedRoute>
                }
              />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/profile/sessions" element={<SessionsPage />} />
              <Route path="/profile/2fa" element={<TwoFactorPage />} />
              <Route path="/profile/login-history" element={<LoginHistoryPage />} />
              <Route
                path="/submissions"
                element={
                  <ProtectedRoute roles={['STD']}>
                    <StudentSubmissionPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/justification"
                element={
                  <ProtectedRoute roles={['PAR']}>
                    <ParentJustificationPage />
                  </ProtectedRoute>
                }
              />
              {/* Rubrics routes */}
              <Route
                path="/rubrics"
                element={
                  <ProtectedRoute roles={['TCH', 'ADM', 'DIR']}>
                    <RubricsListPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/rubrics/:id/edit"
                element={
                  <ProtectedRoute roles={['TCH', 'ADM', 'DIR']}>
                    <RubricEditorPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/rubrics/:id/grade"
                element={
                  <ProtectedRoute roles={['TCH', 'ADM', 'DIR']}>
                    <RubricGradingPage />
                  </ProtectedRoute>
                }
              />
              {/* Question Bank routes */}
              <Route
                path="/question-bank"
                element={
                  <ProtectedRoute roles={['TCH', 'ADM', 'DIR', 'CONTENT_MGR']}>
                    <QuestionBankPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/question-bank/import"
                element={
                  <ProtectedRoute roles={['TCH', 'ADM', 'DIR', 'CONTENT_MGR']}>
                    <QuestionBankImportPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/question-bank/generate"
                element={
                  <ProtectedRoute roles={['TCH', 'ADM', 'DIR', 'CONTENT_MGR']}>
                    <GenerateQuizPage />
                  </ProtectedRoute>
                }
              />
            </Route>

            {/* CMS routes (CONTENT_MGR) — separate layout */}
            <Route
              element={
                <ProtectedRoute roles={['CONTENT_MGR']}>
                  <CmsLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/cms" element={<CmsContentListPage />} />
              <Route path="/cms/upload" element={<CmsContentUploadPage />} />
              <Route path="/cms/content/:contentId/edit" element={<CmsContentEditPage />} />
              <Route path="/cms/review" element={<CmsReviewQueuePage />} />
              <Route path="/cms/quizzes" element={<CmsQuizBuilderPage />} />
              <Route path="/cms/quizzes/:quizId/edit" element={<CmsQuizBuilderPage />} />
              <Route path="/cms/analytics" element={<CmsAnalyticsPage />} />
            </Route>

            {/* Root redirect */}
            <Route path="/" element={<RoleRedirect />} />

            {/* Catch-all → redirect to root */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </ErrorBoundary>
    </div>
  );
}

export default App;
