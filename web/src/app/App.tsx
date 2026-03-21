/**
 * École Platform — Application Root with Routing
 *
 * Reference: S-080 — Route guards, S-079 — Login, S-081 — Feature pages
 * Feature-first architecture per Pack E1.
 * Role-based redirect on root /.
 */

import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '@/services/auth/AuthContext';
import { Layout } from '@/shared/ui/Layout';
import { LoginPage, ROLE_REDIRECT } from '@/features/auth/LoginPage';
import { ProtectedRoute } from '@/features/auth/ProtectedRoute';
import { FeedPage } from '@/features/feed/FeedPage';
import { NotificationsPage } from '@/features/notifications/NotificationsPage';
import { ContentPage } from '@/features/content/ContentPage';
import { ResultsPage } from '@/features/results/ResultsPage';
import { InvoicesPage } from '@/features/invoices/InvoicesPage';
import { ActivitiesPage } from '@/features/activities/ActivitiesPage';
import { ProfilePage } from '@/features/profile/ProfilePage';
import { SessionsPage } from '@/features/profile/SessionsPage';
import { TwoFactorPage } from '@/features/profile/TwoFactorPage';
import { StudentSubmissionPage } from '@/features/submissions/StudentSubmissionPage';
import { ParentJustificationPage } from '@/features/attendance/ParentJustificationPage';
import { DashboardPage } from '@/features/admin/DashboardPage';
import { UsersPage } from '@/features/admin/UsersPage';
import { InvitationsPage } from '@/features/admin/InvitationsPage';
import { AuditLogPage } from '@/features/admin/AuditLogPage';
import { SchoolSettingsPage } from '@/features/admin/SchoolSettingsPage';
import { JustificationReviewPage } from '@/features/admin/JustificationReviewPage';
import { AnalyticsPage } from '@/features/admin/AnalyticsPage';
import { BatchRegisterPage } from '@/features/admin/BatchRegisterPage';
import { RegisterPage } from '@/features/auth/RegisterPage';
import { ClassesPage as TeacherClassesPage } from '@/features/teacher/ClassesPage';
import { CoursesPage as TeacherCoursesPage } from '@/features/teacher/CoursesPage';
import { AssignmentFormPage } from '@/features/teacher/AssignmentFormPage';
import { SubmissionsPage as TeacherSubmissionsPage } from '@/features/teacher/SubmissionsPage';
import { AttendancePage } from '@/features/teacher/AttendancePage';
import { AssessmentFormPage } from '@/features/teacher/AssessmentFormPage';
import { LoadingState } from '@/shared/ui/LoadingState';

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
              <AnalyticsPage />
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
              <AttendancePage />
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
            <ProtectedRoute roles={['PAR', 'TCH', 'ADM', 'DIR']}>
              <NotificationsPage />
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

      {/* Root redirect */}
      <Route path="/" element={<RoleRedirect />} />

      {/* Catch-all → redirect to root */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
