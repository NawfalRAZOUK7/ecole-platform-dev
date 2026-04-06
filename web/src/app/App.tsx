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
import { LoginPage, ROLE_REDIRECT } from '@/features/auth/LoginPage';
import { ProtectedRoute } from '@/features/auth/ProtectedRoute';
import { FeedPage } from '@/features/feed/FeedPage';
import { NotificationsPage } from '@/features/notifications/NotificationsPage';
import { NotificationSettingsPage } from '@/features/notifications/NotificationSettingsPage';
import { ReportsPage } from '@/features/reports/ReportsPage';
import { CalendarPage } from '@/features/calendar/CalendarPage';
import { EventDetailPage } from '@/features/calendar/EventDetailPage';
import { ContentPage } from '@/features/content/ContentPage';
import { ResultsPage } from '@/features/results/ResultsPage';
import { InvoiceDetailPage } from '@/features/invoices/InvoiceDetailPage';
import { InvoicesPage } from '@/features/invoices/InvoicesPage';
import { ActivitiesPage } from '@/features/activities/ActivitiesPage';
import { ProfilePage } from '@/features/profile/ProfilePage';
import { SessionsPage } from '@/features/profile/SessionsPage';
import { TwoFactorPage } from '@/features/profile/TwoFactorPage';
import { StudentSubmissionPage } from '@/features/submissions/StudentSubmissionPage';
import { AttendanceAnalyticsPage } from '@/features/attendance/AttendanceAnalyticsPage';
import { AttendanceHistoryPage } from '@/features/attendance/AttendanceHistoryPage';
import { AttendancePage as AttendanceModulePage } from '@/features/attendance/AttendancePage';
import { ParentJustificationPage } from '@/features/attendance/ParentJustificationPage';
import { GradeDetailPage } from '@/features/gradebook/GradeDetailPage';
import { GradebookPage } from '@/features/gradebook/GradebookPage';
import { DashboardPage } from '@/features/admin/DashboardPage';
import { UsersPage } from '@/features/admin/UsersPage';
import { InvitationsPage } from '@/features/admin/InvitationsPage';
import { AuditLogPage } from '@/features/admin/AuditLogPage';
import { SchoolSettingsPage } from '@/features/admin/SchoolSettingsPage';
import { JustificationReviewPage } from '@/features/admin/JustificationReviewPage';
import { BatchRegisterPage } from '@/features/admin/BatchRegisterPage';
import { ParentChildLinksPage } from '@/features/admin/ParentChildLinksPage';
import { RegisterPage } from '@/features/auth/RegisterPage';
import { ClassesPage as TeacherClassesPage } from '@/features/teacher/ClassesPage';
import { CoursesPage as TeacherCoursesPage } from '@/features/teacher/CoursesPage';
import { AssignmentFormPage } from '@/features/teacher/AssignmentFormPage';
import { SubmissionsPage as TeacherSubmissionsPage } from '@/features/teacher/SubmissionsPage';
import { AttendancePage as TeacherAttendancePage } from '@/features/teacher/AttendancePage';
import { AssessmentFormPage } from '@/features/teacher/AssessmentFormPage';
import { ContentLibraryPage } from '@/features/teacher/ContentLibraryPage';
import { QuizManagerPage } from '@/features/teacher/QuizManagerPage';
import { ContentViewPage } from '@/features/student/ContentViewPage';
import { QuizPlayerPage } from '@/features/student/QuizPlayerPage';
import { LoadingState } from '@/shared/ui/LoadingState';
import { CmsLayout } from '@/features/cms/CmsLayout';
import { CmsContentListPage } from '@/features/cms/ContentListPage';
import { CmsContentUploadPage } from '@/features/cms/ContentUploadPage';
import { CmsContentEditPage } from '@/features/cms/ContentEditPage';
import { CmsReviewQueuePage } from '@/features/cms/ReviewQueuePage';
import { CmsQuizBuilderPage } from '@/features/cms/QuizBuilderPage';
import { CmsAnalyticsPage } from '@/features/cms/AnalyticsPage';
import { TimetablePage } from '@/features/timetable/TimetablePage';
import { FeeStructuresPage } from '@/features/billing/FeeStructuresPage';
import { FeeAssignmentsPage } from '@/features/billing/FeeAssignmentsPage';
import { GenerateInvoicesPage } from '@/features/billing/GenerateInvoicesPage';
import { ConversationsPage } from '@/features/messages/ConversationsPage';
import { ChatPage } from '@/features/messages/ChatPage';
import { AnnouncementsPage } from '@/features/announcements/AnnouncementsPage';
import { ProgressDashboardPage } from '@/features/progress/ProgressDashboardPage';
import { ParentProgressPage } from '@/features/progress/ParentProgressPage';
import { ClassProgressPage } from '@/features/teacher/ClassProgressPage';
import { AnalyticsDashboardPage } from '@/features/analytics/AnalyticsDashboardPage';
import { DocumentsPage } from '@/features/documents/DocumentsPage';
import { ResourcesPage } from '@/features/documents/ResourcesPage';

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

        {/* Timetable (all roles) */}
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
          path="/timetable"
          element={
            <ProtectedRoute roles={['ADM', 'DIR', 'TCH', 'STD', 'PAR']}>
              <TimetablePage />
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
          path="/settings/notifications"
          element={
            <ProtectedRoute roles={['PAR', 'TCH', 'ADM', 'DIR', 'STD']}>
              <NotificationSettingsPage />
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
          path="/results"
          element={
            <ProtectedRoute roles={['STD', 'PAR']}>
              <ResultsPage />
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
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/profile/sessions" element={<SessionsPage />} />
        <Route path="/profile/2fa" element={<TwoFactorPage />} />
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
