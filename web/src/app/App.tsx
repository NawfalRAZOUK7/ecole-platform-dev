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

      {/* Protected routes with layout */}
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
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
      </Route>

      {/* Root redirect */}
      <Route path="/" element={<RoleRedirect />} />

      {/* Catch-all → redirect to root */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
