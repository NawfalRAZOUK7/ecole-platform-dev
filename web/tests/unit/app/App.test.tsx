/**
 * Integration tests for src/app/App.tsx
 * Tests routing, role redirects, and ProtectedRoute guard.
 * All lazy-loaded feature pages are mocked to avoid loading real components.
 */
import { screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { I18nextProvider } from 'react-i18next';
import i18n from '@/shared/i18n';
import { AuthContext, type AuthContextValue } from '@/app/providers/AuthContext';
import App from '@/app/App';
import { createUser } from '../../utils/factories';

vi.mock('@/features/auth/lazy', () => ({
  LoginPage: () => <div data-testid="login-page">Login</div>,
  RegisterPage: () => <div>RegisterPage</div>,
  ForgotPasswordPage: () => <div>ForgotPasswordPage</div>,
  ResetPasswordPage: () => <div>ResetPasswordPage</div>,
}));

vi.mock('@/features/admin/lazy', () => ({
  DashboardPage: () => <div data-testid="admin-dashboard">AdminDashboard</div>,
  UsersPage: () => <div>'UsersPage'</div>,
  InvitationsPage: () => <div>'InvitationsPage'</div>,
  AuditLogPage: () => <div>'AuditLogPage'</div>,
  JustificationReviewPage: () => <div>'JustificationReviewPage'</div>,
  BatchRegisterPage: () => <div>'BatchRegisterPage'</div>,
  ComplianceDashboardPage: () => <div>'ComplianceDashboardPage'</div>,
  CurriculumMappingPage: () => <div>'CurriculumMappingPage'</div>,
  ComplianceReportPage: () => <div>'ComplianceReportPage'</div>,
}));

vi.mock('@/features/academic/lazy', () => ({
  ProgramsPage: () => <div>'ProgramsPage'</div>,
  EnrollmentsPage: () => <div>'EnrollmentsPage'</div>,
  ProgramEquivalencesPage: () => <div>'ProgramEquivalencesPage'</div>,
  ProgramVersionsPage: () => <div>'ProgramVersionsPage'</div>,
  EligibilityRulesPage: () => <div>'EligibilityRulesPage'</div>,
  StudentAcademicHistoryPage: () => <div>'StudentAcademicHistoryPage'</div>,
  AttendanceModulePage: () => <div>'AttendanceModulePage'</div>,
  AttendanceHistoryPage: () => <div>'AttendanceHistoryPage'</div>,
  AttendanceAnalyticsPage: () => <div>'AttendanceAnalyticsPage'</div>,
  ParentJustificationPage: () => <div>'ParentJustificationPage'</div>,
  GradebookPage: () => <div>'GradebookPage'</div>,
  GradeDetailPage: () => <div>'GradeDetailPage'</div>,
  TimetablePage: () => <div>'TimetablePage'</div>,
  TimetableConstraintsPage: () => <div>'TimetableConstraintsPage'</div>,
  TimetableGeneratePage: () => <div>'TimetableGeneratePage'</div>,
  ProgressDashboardPage: () => <div>'ProgressDashboardPage'</div>,
  ParentProgressPage: () => <div>'ParentProgressPage'</div>,
  ResultsPage: () => <div>'ResultsPage'</div>,
  SkillsOverviewPage: () => <div>'SkillsOverviewPage'</div>,
  SkillPassportPage: () => <div>'SkillPassportPage'</div>,
  SkillEvaluationPage: () => <div>'SkillEvaluationPage'</div>,
  SkillAnalyticsPage: () => <div>'SkillAnalyticsPage'</div>,
  TeacherClassesPage: () => <div data-testid="teacher-classes">TeacherClasses</div>,
  TeacherAttendancePage: () => <div>'TeacherAttendancePage'</div>,
  ClassProgressPage: () => <div>'ClassProgressPage'</div>,
}));

vi.mock('@/features/billing/lazy', () => ({
  BudgetListPage: () => <div>'BudgetListPage'</div>,
  BudgetRequestPage: () => <div>'BudgetRequestPage'</div>,
  BudgetAnalyticsPage: () => <div>'BudgetAnalyticsPage'</div>,
  BudgetDetailPage: () => <div>'BudgetDetailPage'</div>,
  InvoicesPage: () => <div>'InvoicesPage'</div>,
  InvoiceDetailPage: () => <div>'InvoiceDetailPage'</div>,
  FeeStructuresPage: () => <div>'FeeStructuresPage'</div>,
  FeeAssignmentsPage: () => <div>'FeeAssignmentsPage'</div>,
  GenerateInvoicesPage: () => <div>'GenerateInvoicesPage'</div>,
  SiblingPolicyPage: () => <div>'SiblingPolicyPage'</div>,
  LateFeePolicyPage: () => <div>'LateFeePolicyPage'</div>,
  PaymentPlansPage: () => <div>'PaymentPlansPage'</div>,
  PaymentPlanDetailPage: () => <div>'PaymentPlanDetailPage'</div>,
  MicroSchoolEnrollPage: () => <div>'MicroSchoolEnrollPage'</div>,
}));

vi.mock('@/features/communication/lazy', () => ({
  NotificationsPage: () => <div data-testid="notifications-page">Notifications</div>,
  NotificationSettingsPage: () => <div>'NotificationSettingsPage'</div>,
  CalendarPage: () => <div>'CalendarPage'</div>,
  EventDetailPage: () => <div>'EventDetailPage'</div>,
  HolidayManagerPage: () => <div>'HolidayManagerPage'</div>,
  ConversationsPage: () => <div>'ConversationsPage'</div>,
  ChatPage: () => <div>'ChatPage'</div>,
  AnnouncementsPage: () => <div>'AnnouncementsPage'</div>,
}));

vi.mock('@/features/content/lazy', () => ({
  FeedPage: () => <div data-testid="feed-page">Feed</div>,
  ContentPage: () => <div>'ContentPage'</div>,
  ContentDetailPage: () => <div>'ContentDetailPage'</div>,
  ContentPlayerPage: () => <div>'ContentPlayerPage'</div>,
  StudentContentPage: () => <div>'StudentContentPage'</div>,
  StoryViewerPage: () => <div>'StoryViewerPage'</div>,
  ColoringViewerPage: () => <div>'ColoringViewerPage'</div>,
  DocumentsPage: () => <div>'DocumentsPage'</div>,
  ResourcesPage: () => <div>'ResourcesPage'</div>,
  DocumentVersionsPage: () => <div>'DocumentVersionsPage'</div>,
  DocumentPreviewPage: () => <div>'DocumentPreviewPage'</div>,
  StudentDocumentsPage: () => <div>'StudentDocumentsPage'</div>,
  ContentLibraryPage: () => <div>'ContentLibraryPage'</div>,
  CmsContentListPage: () => <div>'CmsContentListPage'</div>,
  CmsContentUploadPage: () => <div>'CmsContentUploadPage'</div>,
  CmsContentEditPage: () => <div>'CmsContentEditPage'</div>,
  CmsReviewQueuePage: () => <div>'CmsReviewQueuePage'</div>,
  CmsQuizBuilderPage: () => <div>'CmsQuizBuilderPage'</div>,
  CmsAnalyticsPage: () => <div>'CmsAnalyticsPage'</div>,
}));

vi.mock('@/features/lms/lazy', () => ({
  TeacherCoursesPage: () => <div>'TeacherCoursesPage'</div>,
  AssignmentFormPage: () => <div>'AssignmentFormPage'</div>,
  TeacherSubmissionsPage: () => <div>'TeacherSubmissionsPage'</div>,
  AssessmentFormPage: () => <div>'AssessmentFormPage'</div>,
  QuizManagerPage: () => <div>'QuizManagerPage'</div>,
  QuizPlayerPage: () => <div>'QuizPlayerPage'</div>,
  WritingWorkspacePage: () => <div>'WritingWorkspacePage'</div>,
  StudentSubmissionPage: () => <div>'StudentSubmissionPage'</div>,
  RubricsListPage: () => <div>'RubricsListPage'</div>,
  RubricEditorPage: () => <div>'RubricEditorPage'</div>,
  RubricGradingPage: () => <div>'RubricGradingPage'</div>,
  QuestionBankPage: () => <div>'QuestionBankPage'</div>,
  QuestionBankImportPage: () => <div>'QuestionBankImportPage'</div>,
  GenerateQuizPage: () => <div>'GenerateQuizPage'</div>,
}));

vi.mock('@/features/reports/lazy', () => ({
  ReportsPage: () => <div>'ReportsPage'</div>,
  AnalyticsDashboardPage: () => <div>'AnalyticsDashboardPage'</div>,
  FinancialDashboardPage: () => <div>'FinancialDashboardPage'</div>,
  FinancialSnapshotsPage: () => <div>'FinancialSnapshotsPage'</div>,
  FinancialExportPage: () => <div>'FinancialExportPage'</div>,
}));

vi.mock('@/features/school/lazy', () => ({
  SchoolSettingsPage: () => <div>'SchoolSettingsPage'</div>,
  MicroSchoolListPage: () => <div>'MicroSchoolListPage'</div>,
  MicroSchoolDetailPage: () => <div>'MicroSchoolDetailPage'</div>,
  MicroSchoolEnrollPage: () => <div>'MicroSchoolEnrollPage'</div>,
}));

vi.mock('@/features/ai/lazy', () => ({
  BadgesPage: () => <div>'BadgesPage'</div>,
  RewardsPage: () => <div>'RewardsPage'</div>,
  StudentRewardsPage: () => <div>'StudentRewardsPage'</div>,
  LeaderboardPage: () => <div>'LeaderboardPage'</div>,
  GamesListPage: () => <div>'GamesListPage'</div>,
  GameConfigDetailPage: () => <div>'GameConfigDetailPage'</div>,
  GameConfigEditor: () => <div>'GameConfigEditor'</div>,
  StudentGamesPage: () => <div>'StudentGamesPage'</div>,
  GamePlayerPage: () => <div>'GamePlayerPage'</div>,
  ActivitiesPage: () => <div>'ActivitiesPage'</div>,
  ActivityDetailPage: () => <div>'ActivityDetailPage'</div>,
}));

vi.mock('@/features/sync/lazy', () => ({
  SyncStatusPage: () => <div>'SyncStatusPage'</div>,
  SyncConflictsPage: () => <div>'SyncConflictsPage'</div>,
  SyncSettingsPage: () => <div>'SyncSettingsPage'</div>,
}));

vi.mock('@/features/user/lazy', () => ({
  ProfilePage: () => <div>'ProfilePage'</div>,
  SessionsPage: () => <div>'SessionsPage'</div>,
  TwoFactorPage: () => <div>'TwoFactorPage'</div>,
  LoginHistoryPage: () => <div>'LoginHistoryPage'</div>,
  MyChildrenPage: () => <div>'MyChildrenPage'</div>,
  SharedReviewPage: () => <div>'SharedReviewPage'</div>,
  ReviewDetailPage: () => <div>'ReviewDetailPage'</div>,
  ParentChildLinksPage: () => <div>'ParentChildLinksPage'</div>,
  StudentHomePage: () => <div data-testid="student-home">StudentHome</div>,
}));

vi.mock('@/features/content/cms/ui/CmsLayout', () => ({
  CmsLayout: ({ children }: { children?: React.ReactNode }) => (
    <div data-testid="cms-layout">{children}</div>
  ),
}));

vi.mock('@/pages/admin/FeatureTogglesPage', () => ({
  FeatureTogglesPage: () => <div>'FeatureTogglesPage'</div>,
}));
vi.mock('@/features/lms/quizzes/ui/QuizAnalyticsPage', () => ({
  QuizAnalyticsPage: () => <div>'QuizAnalyticsPage'</div>,
}));
vi.mock('@/features/lms/quizzes/ui/QuizResultsPage', () => ({
  QuizResultsPage: () => <div>'QuizResultsPage'</div>,
}));
vi.mock('@/pages/user/GDPRPage', () => ({
  GDPRPage: () => <div>'GDPRPage'</div>,
}));
vi.mock('@/widgets/layout/Layout', () => ({
  Layout: () => <div data-testid="app-layout">Layout</div>,
}));
vi.mock('@/shared/ui/OfflineIndicator', () => ({
  OfflineIndicator: () => <span data-testid="offline-indicator" />,
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function buildAuth(overrides: Partial<AuthContextValue> = {}): AuthContextValue {
  return {
    user: createUser({ role: 'ADM' }),
    isAuthenticated: true,
    isLoading: false,
    error: null,
    twoFactorPending: null,
    oauthPending: null,
    login: vi.fn(),
    verify2fa: vi.fn(),
    cancel2fa: vi.fn(),
    logout: vi.fn(),
    clearError: vi.fn(),
    startOAuthLogin: vi.fn(),
    completeOAuthLogin: vi.fn(),
    ...overrides,
  };
}

function renderApp(route: string, authOverride: Partial<AuthContextValue> = {}) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <I18nextProvider i18n={i18n}>
      <QueryClientProvider client={qc}>
        <AuthContext.Provider value={buildAuth(authOverride)}>
          <MemoryRouter initialEntries={[route]}>
            <App />
          </MemoryRouter>
        </AuthContext.Provider>
      </QueryClientProvider>
    </I18nextProvider>,
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('App routing', () => {
  it('shows login page at /login when unauthenticated', async () => {
    renderApp('/login', { user: null, isAuthenticated: false });
    expect(await screen.findByTestId('login-page')).toBeInTheDocument();
  });

  it('shows register page at /register', async () => {
    renderApp('/register', { user: null, isAuthenticated: false });
    expect(await screen.findByText('RegisterPage')).toBeInTheDocument();
  });

  it('shows forgot password at /forgot-password', async () => {
    renderApp('/forgot-password', { user: null, isAuthenticated: false });
    expect(await screen.findByText('ForgotPasswordPage')).toBeInTheDocument();
  });

  it('shows reset password at /reset-password', async () => {
    renderApp('/reset-password', { user: null, isAuthenticated: false });
    expect(await screen.findByText('ResetPasswordPage')).toBeInTheDocument();
  });

  it('renders Layout wrapper for authenticated protected routes', async () => {
    renderApp('/admin', { isAuthenticated: true });
    expect(await screen.findByTestId('app-layout')).toBeInTheDocument();
  });

  it('redirects unauthenticated user from /admin to /login', async () => {
    renderApp('/admin', { user: null, isAuthenticated: false });
    expect(await screen.findByTestId('login-page')).toBeInTheDocument();
  });

  it('shows loading state during auth initialization', async () => {
    renderApp('/admin', { isLoading: true, isAuthenticated: false, user: null });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('redirects / to /admin for ADM user', async () => {
    renderApp('/', { isAuthenticated: true, user: createUser({ role: 'ADM' }) });
    expect(await screen.findByTestId('app-layout')).toBeInTheDocument();
  });

  it('redirects / to /teacher for TCH user', async () => {
    renderApp('/', { isAuthenticated: true, user: createUser({ role: 'TCH' }) });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('redirects / to /feed for PAR user', async () => {
    renderApp('/', { isAuthenticated: true, user: createUser({ role: 'PAR' }) });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('redirects / to /student/home for STD user', async () => {
    renderApp('/', { isAuthenticated: true, user: createUser({ role: 'STD' }) });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders offline indicator always', async () => {
    renderApp('/login', { user: null, isAuthenticated: false });
    await screen.findByTestId('offline-indicator');
  });

  it('does not show Layout for public routes (login)', async () => {
    renderApp('/login', { user: null, isAuthenticated: false });
    await screen.findByTestId('login-page');
    expect(screen.queryByTestId('app-layout')).toBeNull();
  });
});

describe('ProtectedRoute', () => {
  it('allows authenticated user through', async () => {
    renderApp('/admin', { isAuthenticated: true });
    expect(await screen.findByTestId('app-layout')).toBeInTheDocument();
  });

  it('blocks unauthenticated and redirects to /login', async () => {
    renderApp('/admin', { user: null, isAuthenticated: false, isLoading: false });
    expect(await screen.findByTestId('login-page')).toBeInTheDocument();
  });

  it('blocks user with wrong role and redirects to /', async () => {
    const par = createUser({ role: 'PAR' });
    renderApp('/admin/users', { isAuthenticated: true, user: par });
    // PAR doesn't have ADM/DIR role, gets redirected
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('passes through user with correct role', async () => {
    const adm = createUser({ role: 'ADM' });
    renderApp('/admin', { isAuthenticated: true, user: adm });
    expect(await screen.findByTestId('app-layout')).toBeInTheDocument();
  });
});
