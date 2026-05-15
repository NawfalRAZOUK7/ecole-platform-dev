/**
 * Protected route guard — auth + optional role check.
 *
 * Reference: S-080 — Route guards with auth + role check
 * Redirects to /login if not authenticated.
 * Redirects to / if authenticated but wrong role.
 */

import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/app/providers/AuthContext';
import { LoadingState } from '@/shared/ui/LoadingState';

interface ProtectedRouteProps {
  children: React.ReactNode;
  roles?: string[];
}

export function ProtectedRoute({ children, roles }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingState />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (roles && roles.length > 0 && user && !roles.includes(user.role)) {
    // User is authenticated but lacks the required role — redirect to home
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
