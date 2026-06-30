import { describe, it, expect } from 'vitest';
import { ROUTES, type AppRoute } from '@/app/routes';

describe('ROUTES', () => {
  it('has required auth routes', () => {
    expect(ROUTES.HOME).toBe('/');
    expect(ROUTES.LOGIN).toBe('/login');
    expect(ROUTES.REGISTER).toBe('/register');
    expect(ROUTES.VERIFY_2FA).toBe('/verify-2fa');
    expect(ROUTES.DASHBOARD).toBe('/dashboard');
  });

  it('has admin routes', () => {
    expect(ROUTES.ADMIN).toBe('/admin');
    expect(ROUTES.ADMIN_USERS).toBe('/admin/users');
    expect(ROUTES.ADMIN_INVITATIONS).toBe('/admin/invitations');
    expect(ROUTES.ADMIN_AUDIT).toBe('/admin/audit');
    expect(ROUTES.ADMIN_SETTINGS).toBe('/admin/school');
    expect(ROUTES.ADMIN_BADGES).toBe('/admin/badges');
    expect(ROUTES.ADMIN_JUSTIFICATIONS).toBe('/admin/justifications');
    expect(ROUTES.ADMIN_ANALYTICS).toBe('/admin/analytics');
    expect(ROUTES.ADMIN_BATCH_REGISTER).toBe('/admin/batch-register');
    expect(ROUTES.ADMIN_FAMILY_LINKS).toBe('/admin/family-links');
    expect(ROUTES.ADMIN_PROGRAMS).toBe('/admin/programs');
    expect(ROUTES.ADMIN_ENROLLMENTS).toBe('/admin/enrollments');
    expect(ROUTES.ADMIN_EQUIVALENCES).toBe('/admin/program-equivalences');
    expect(ROUTES.ADMIN_PROGRAM_VERSIONS).toBe('/admin/programs/:programId/versions');
    expect(ROUTES.ADMIN_ELIGIBILITY_RULES).toBe('/admin/eligibility-rules');
  });

  it('has student routes', () => {
    expect(ROUTES.STUDENT_HOME).toBe('/student/home');
    expect(ROUTES.STUDENT_CONTENT).toBe('/student/content');
    expect(ROUTES.STUDENT_QUIZZES).toBe('/student/quizzes');
    expect(ROUTES.STUDENT_ACADEMIC_HISTORY).toBe('/students/:studentId/academic-history');
  });

  it('has teacher routes', () => {
    expect(ROUTES.TEACHER_CLASSES).toBe('/teacher');
    expect(ROUTES.TEACHER_COURSES).toBe('/teacher/courses');
    expect(ROUTES.TEACHER_ASSIGNMENTS).toBe('/teacher/assignments');
    expect(ROUTES.TEACHER_SUBMISSIONS).toBe('/teacher/submissions');
    expect(ROUTES.TEACHER_ATTENDANCE).toBe('/teacher/attendance');
    expect(ROUTES.TEACHER_ASSESSMENTS).toBe('/teacher/assessments');
    expect(ROUTES.TEACHER_CONTENT_LIBRARY).toBe('/teacher/content-library');
    expect(ROUTES.TEACHER_QUIZZES).toBe('/teacher/quizzes');
    expect(ROUTES.TEACHER_CLASS_PROGRESS).toBe('/teacher/class-progress');
  });

  it('has academic routes', () => {
    expect(ROUTES.ATTENDANCE).toBe('/attendance');
    expect(ROUTES.ATTENDANCE_HISTORY).toBe('/attendance/history');
    expect(ROUTES.ATTENDANCE_ANALYTICS).toBe('/attendance/analytics');
    expect(ROUTES.GRADEBOOK).toBe('/gradebook');
    expect(ROUTES.GRADEBOOK_STUDENT).toBe('/gradebook/student/:studentId');
    expect(ROUTES.TIMETABLE).toBe('/timetable');
    expect(ROUTES.SKILLS).toBe('/skills');
    expect(ROUTES.SKILL_PASSPORT).toBe('/skills/passport/:studentId');
  });

  it('has billing routes', () => {
    expect(ROUTES.INVOICES).toBe('/invoices');
    expect(ROUTES.INVOICE_DETAIL).toBe('/invoices/:id');
    expect(ROUTES.BUDGETS).toBe('/budgets');
    expect(ROUTES.BUDGET_DETAIL).toBe('/budgets/:id');
    expect(ROUTES.BUDGET_REQUESTS).toBe('/budgets/requests');
    expect(ROUTES.BUDGET_ANALYTICS).toBe('/budgets/analytics');
  });

  it('has communication routes', () => {
    expect(ROUTES.MESSAGES).toBe('/messages');
    expect(ROUTES.MESSAGE_DETAIL).toBe('/messages/:conversationId');
    expect(ROUTES.ANNOUNCEMENTS).toBe('/announcements');
    expect(ROUTES.NOTIFICATIONS).toBe('/notifications');
    expect(ROUTES.NOTIFICATION_SETTINGS).toBe('/settings/notifications');
  });

  it('has CMS routes', () => {
    expect(ROUTES.CMS).toBe('/cms');
    expect(ROUTES.CMS_UPLOAD).toBe('/cms/upload');
    expect(ROUTES.CMS_EDIT).toBe('/cms/content/:contentId/edit');
    expect(ROUTES.CMS_REVIEW).toBe('/cms/review');
    expect(ROUTES.CMS_QUIZZES).toBe('/cms/quizzes');
    expect(ROUTES.CMS_QUIZ_EDIT).toBe('/cms/quizzes/:quizId/edit');
    expect(ROUTES.CMS_ANALYTICS).toBe('/cms/analytics');
  });

  it('has profile routes', () => {
    expect(ROUTES.PROFILE).toBe('/profile');
    expect(ROUTES.PROFILE_SESSIONS).toBe('/profile/sessions');
    expect(ROUTES.PROFILE_2FA).toBe('/profile/2fa');
  });

  it('has content routes', () => {
    expect(ROUTES.CONTENT).toBe('/content');
    expect(ROUTES.CONTENT_DETAIL).toBe('/content/:id');
    expect(ROUTES.CONTENT_PLAYER).toBe('/content/:id/play');
  });

  it('has micro-school routes', () => {
    expect(ROUTES.MICRO_SCHOOLS).toBe('/micro-schools');
    expect(ROUTES.MICRO_SCHOOL_DETAIL).toBe('/micro-schools/:id');
    expect(ROUTES.MICRO_SCHOOL_ENROLL).toBe('/micro-schools/:id/enroll');
  });

  it('has games routes', () => {
    expect(ROUTES.GAMES).toBe('/teacher/games');
    expect(ROUTES.GAMES_LEGACY).toBe('/games');
    expect(ROUTES.GAMES_NEW).toBe('/teacher/games/new');
    expect(ROUTES.GAMES_DETAIL).toBe('/teacher/games/:id');
  });

  it('has fee management routes', () => {
    expect(ROUTES.ADMIN_FEE_STRUCTURES).toBe('/admin/fee-structures');
    expect(ROUTES.ADMIN_FEE_ASSIGNMENTS).toBe('/admin/fee-assignments');
    expect(ROUTES.ADMIN_GENERATE_INVOICES).toBe('/admin/generate-invoices');
  });

  it('has sync routes', () => {
    expect(ROUTES.SYNC).toBe('/sync');
    expect(ROUTES.SYNC_CONFLICTS).toBe('/sync/conflicts');
    expect(ROUTES.SYNC_SETTINGS).toBe('/sync/settings');
  });

  it('all values are strings', () => {
    Object.values(ROUTES).forEach((value) => {
      expect(typeof value).toBe('string');
    });
  });

  it('all routes start with /', () => {
    Object.values(ROUTES).forEach((value) => {
      expect(value).toMatch(/^\//);
    });
  });

  it('AppRoute type covers all route values', () => {
    // Verify the type is derived from ROUTES
    const routes: AppRoute = ROUTES.HOME;
    expect(routes).toBe('/');
  });

  it('has unique route values', () => {
    const values = Object.values(ROUTES);
    const unique = new Set(values);
    expect(unique.size).toBe(values.length);
  });

  it('has rewards and gamification routes', () => {
    expect(ROUTES.FEED).toBe('/feed');
    expect(ROUTES.REWARDS).toBe('/rewards');
    expect(ROUTES.STUDENT_REWARDS).toBe('/students/:id/rewards');
    expect(ROUTES.CLASS_LEADERBOARD).toBe('/classes/:classId/leaderboard');
  });
});
