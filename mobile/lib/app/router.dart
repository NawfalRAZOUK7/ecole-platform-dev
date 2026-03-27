/// App router — go_router with auth guards and deep-link support.
///
/// Reference: DEC-E2-010 — Declarative routing with auth guards
/// Routes redirect to /login if not authenticated.
/// Role-based home redirect (PAR→/feed, STD→/content, etc.)
/// Phase 5A: Added 2FA setup, password change, submission upload routes.
/// Phase 5B: Added admin + teacher routes.
/// Phase 10C: Added content library, student content, quiz player routes.

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/features/auth/login_screen.dart';
import 'package:ecole_platform/features/auth/register_screen.dart';
import 'package:ecole_platform/features/feed/feed_screen.dart';
import 'package:ecole_platform/features/notifications/notifications_screen.dart';
import 'package:ecole_platform/features/notifications/notification_preferences_screen.dart';
import 'package:ecole_platform/features/calendar/calendar_screen.dart';
import 'package:ecole_platform/features/calendar/event_detail_screen.dart';
import 'package:ecole_platform/features/calendar/create_event_screen.dart';
import 'package:ecole_platform/features/content/content_screen.dart';
import 'package:ecole_platform/features/results/results_screen.dart';
import 'package:ecole_platform/features/invoices/invoices_screen.dart';
import 'package:ecole_platform/features/profile/profile_screen.dart';
import 'package:ecole_platform/features/profile/two_factor_setup_screen.dart';
import 'package:ecole_platform/features/profile/change_password_screen.dart';
import 'package:ecole_platform/features/submissions/submission_upload_screen.dart';
import 'package:ecole_platform/features/admin/admin_dashboard_screen.dart';
import 'package:ecole_platform/features/admin/users_screen.dart';
import 'package:ecole_platform/features/admin/invitations_screen.dart';
import 'package:ecole_platform/features/admin/justification_review_screen.dart';
import 'package:ecole_platform/features/teacher/classes_screen.dart';
import 'package:ecole_platform/features/teacher/assignment_form_screen.dart';
import 'package:ecole_platform/features/teacher/submissions_screen.dart';
import 'package:ecole_platform/features/teacher/attendance_screen.dart';
import 'package:ecole_platform/features/teacher/content_library_screen.dart';
import 'package:ecole_platform/features/student/student_content_screen.dart';
import 'package:ecole_platform/features/student/quiz_player_screen.dart';
import 'package:ecole_platform/features/family/my_children_screen.dart';
import 'package:ecole_platform/features/timetable/timetable_screen.dart';
import 'package:ecole_platform/features/messages/conversations_screen.dart';
import 'package:ecole_platform/features/messages/chat_screen.dart';
import 'package:ecole_platform/features/messages/announcements_screen.dart';
import 'package:ecole_platform/features/progress/progress_screen.dart';
import 'package:ecole_platform/features/progress/parent_progress_screen.dart';
import 'package:ecole_platform/features/reports/reports_screen.dart';
import 'package:ecole_platform/features/analytics/analytics_summary_screen.dart';
import 'package:ecole_platform/features/documents/documents_screen.dart';
import 'package:ecole_platform/presentation/shell_screen.dart';

/// Role-based redirect targets.
const _roleRedirects = <String, String>{
  'PAR': '/feed',
  'STD': '/student/content',
  'TCH': '/teacher/classes',
  'ADM': '/admin/dashboard',
  'DIR': '/admin/dashboard',
  'SUP': '/notifications',
};

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/login',
    redirect: (context, state) {
      final isAuthenticated = authState.isAuthenticated;
      final isLoading = authState.isLoading;
      final loc = state.matchedLocation;
      final isPublicPage = loc == '/login' || loc == '/register';

      // Still loading — don't redirect
      if (isLoading) return null;

      // Not authenticated + not on public page → go to login
      if (!isAuthenticated && !isPublicPage) return '/login';

      // Authenticated + on public page → redirect to role home
      if (isAuthenticated && isPublicPage) {
        final role = authState.user?.role ?? '';
        return _roleRedirects[role] ?? '/profile';
      }

      return null; // no redirect needed
    },
    routes: [
      // Login (no shell)
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),

      // Register (no shell) — Phase 5C
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),

      // Shell with bottom navigation
      ShellRoute(
        builder: (context, state, child) => ShellScreen(child: child),
        routes: [
          // ── Admin routes ──
          GoRoute(
            path: '/admin/dashboard',
            builder: (context, state) => const AdminDashboardScreen(),
          ),
          GoRoute(
            path: '/admin/users',
            builder: (context, state) => const UsersScreen(),
          ),
          GoRoute(
            path: '/admin/invitations',
            builder: (context, state) => const InvitationsScreen(),
          ),
          GoRoute(
            path: '/admin/justifications',
            builder: (context, state) => const JustificationReviewScreen(),
          ),
          GoRoute(
            path: '/analytics',
            builder: (context, state) => const AnalyticsSummaryScreen(),
          ),

          // ── Teacher routes ──
          GoRoute(
            path: '/teacher/classes',
            builder: (context, state) => const ClassesScreen(),
          ),
          GoRoute(
            path: '/teacher/assignments',
            builder: (context, state) => const AssignmentFormScreen(),
          ),
          GoRoute(
            path: '/teacher/submissions',
            builder: (context, state) => const SubmissionsScreen(),
          ),
          GoRoute(
            path: '/teacher/attendance',
            builder: (context, state) => const AttendanceScreen(),
          ),
          // Phase 10C: Teacher content library
          GoRoute(
            path: '/teacher/content-library',
            builder: (context, state) => const ContentLibraryScreen(),
          ),

          // ── Parent routes ──
          GoRoute(
            path: '/family',
            builder: (context, state) => const MyChildrenScreen(),
          ),

          // ── Student routes (Phase 10C) ──
          GoRoute(
            path: '/student/content',
            builder: (context, state) => const StudentContentScreen(),
          ),
          GoRoute(
            path: '/student/quizzes',
            builder: (context, state) => const QuizPlayerScreen(),
          ),

          // ── Phase 12B routes ──
          GoRoute(
            path: '/timetable',
            builder: (context, state) => const TimetableScreen(),
          ),
          GoRoute(
            path: '/messages',
            builder: (context, state) => const ConversationsScreen(),
          ),
          GoRoute(
            path: '/messages/:id',
            builder: (context, state) => ChatScreen(
              conversationId: state.pathParameters['id']!,
            ),
          ),
          GoRoute(
            path: '/announcements',
            builder: (context, state) => const AnnouncementsScreen(),
          ),

          // ── Phase 12C routes ──
          GoRoute(
            path: '/progress',
            builder: (context, state) => const ProgressScreen(),
          ),
          GoRoute(
            path: '/progress/:studentId',
            builder: (context, state) => ProgressScreen(
              studentId: state.pathParameters['studentId'],
            ),
          ),
          GoRoute(
            path: '/parent/progress',
            builder: (context, state) => const ParentProgressScreen(),
          ),

          // ── Common routes ──
          GoRoute(
            path: '/feed',
            builder: (context, state) => const FeedScreen(),
          ),
          GoRoute(
            path: '/notifications',
            builder: (context, state) => const NotificationsScreen(),
          ),
          GoRoute(
            path: '/calendar',
            builder: (context, state) => const CalendarScreen(),
          ),
          GoRoute(
            path: '/events/:id',
            builder: (context, state) => EventDetailScreen(
              eventId: state.pathParameters['id']!,
            ),
          ),
          GoRoute(
            path: '/events/create',
            builder: (context, state) => CreateEventScreen(
              initialEvent: state.extra as dynamic,
            ),
          ),
          GoRoute(
            path: '/reports',
            builder: (context, state) => const ReportsScreen(),
          ),
          GoRoute(
            path: '/documents',
            builder: (context, state) => const DocumentsScreen(),
          ),
          GoRoute(
            path: '/settings/notifications',
            builder: (context, state) => const NotificationPreferencesScreen(),
          ),
          GoRoute(
            path: '/content',
            builder: (context, state) => const ContentScreen(),
          ),
          GoRoute(
            path: '/results',
            builder: (context, state) => const ResultsScreen(),
          ),
          GoRoute(
            path: '/invoices',
            builder: (context, state) => const InvoicesScreen(),
          ),
          GoRoute(
            path: '/profile',
            builder: (context, state) => const ProfileScreen(),
            routes: [
              GoRoute(
                path: '2fa',
                builder: (context, state) => const TwoFactorSetupScreen(),
              ),
              GoRoute(
                path: 'password',
                builder: (context, state) => const ChangePasswordScreen(),
              ),
            ],
          ),
        ],
      ),

      // Submission upload (outside shell — full screen)
      // Phase 10C: extended with exercise_type + has_exercise_pdf
      GoRoute(
        path: '/submissions/upload',
        builder: (context, state) {
          final extra = state.extra as Map<String, String>?;
          return SubmissionUploadScreen(
            assignmentId: extra?['assignment_id'],
            assignmentTitle: extra?['assignment_title'],
            exerciseType: extra?['exercise_type'],
            hasExercisePdf: extra?['has_exercise_pdf'] == 'true',
          );
        },
      ),
    ],
  );
});
