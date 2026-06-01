import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { attendanceService } from '@/features/academic/attendance/api/attendance.api';
import { gradebookService } from '@/features/academic/gradebook/api/gradebook.api';
import { programsService } from '@/features/academic/programs/api/programs.api';
import { skillsService } from '@/features/academic/skills/api/skills.api';
import { resultsService } from '@/features/academic/results/api/results.api';
import { progressService } from '@/features/academic/progress/api/progress.api';
import { server } from '../../utils/mocks';

const meta = { timestamp: new Date().toISOString(), version: '0.1.0' };
const listMeta = { ...meta, next_cursor: null, has_more: false };

// ── attendanceService ─────────────────────────────────────────────────────────

describe('attendanceService', () => {
  const classAttendance = {
    class_id: 'class-1',
    stats: { total_students: 20, attendance_rate: 90, absent_count: 2, late_count: 0 },
    records: [],
  };

  it('getClassAttendance returns class attendance', async () => {
    server.use(
      http.get('/api/v1/attendance/class/class-1', () =>
        HttpResponse.json({ data: classAttendance, meta }),
      ),
    );
    const result = await attendanceService.getClassAttendance('class-1', '2025-01-07');
    expect(result.data.class_id).toBe('class-1');
    expect(result.data.stats.attendance_rate).toBe(90);
  });

  it('markAttendance posts attendance', async () => {
    server.use(
      http.post('/api/v1/attendance/class/class-1', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await attendanceService.markAttendance({
      class_id: 'class-1',
      date: '2025-01-07',
      records: [{ student_id: 'student-1', status: 'present', absence_reason: null }],
    });
    expect(result).toBeDefined();
  });

  it('submitJustification posts justification', async () => {
    const justification = {
      id: 'just-1',
      attendance_record_id: 'rec-1',
      status: 'pending',
      reason: 'Sick',
      attachment_url: null,
    };
    server.use(
      http.post('/api/v1/attendance/justifications', () =>
        HttpResponse.json({ data: justification, meta }),
      ),
    );
    const result = await attendanceService.submitJustification('rec-1', 'Sick');
    expect(result.data.id).toBe('just-1');
  });

  it('getAttendanceTrends returns trends', async () => {
    server.use(
      http.get('/api/v1/analytics/attendance/trends/class-1', () =>
        HttpResponse.json({ data: [], meta }),
      ),
    );
    const result = await attendanceService.getAttendanceTrends(
      'class-1',
      '2025-01-01',
      '2025-01-31',
    );
    expect(result.data).toEqual([]);
  });

  it('getAttendanceAlerts returns alerts', async () => {
    server.use(
      http.get('/api/v1/analytics/attendance/alerts', () => HttpResponse.json({ data: [], meta })),
    );
    const result = await attendanceService.getAttendanceAlerts('school-1');
    expect(result.data).toEqual([]);
  });

  it('getStudentHistory returns student history', async () => {
    server.use(
      http.get('/api/v1/analytics/attendance/student/student-1', () =>
        HttpResponse.json({ data: [], meta }),
      ),
    );
    const result = await attendanceService.getStudentHistory('student-1');
    expect(result.data).toEqual([]);
  });

  it('getClassStats returns class stats', async () => {
    server.use(
      http.get('/api/v1/analytics/attendance/class/class-1', () =>
        HttpResponse.json({ data: { class_id: 'class-1', attendance_rate: 90 }, meta }),
      ),
    );
    const result = await attendanceService.getClassStats('class-1');
    expect(result.data.attendance_rate).toBe(90);
  });

  it('exportAttendanceAnalytics returns analytics export', async () => {
    server.use(
      http.get('/api/v1/analytics/attendance/class/class-1', () =>
        HttpResponse.json({ data: { class_id: 'class-1', attendance_rate: 90 }, meta }),
      ),
    );
    const result = await attendanceService.exportAttendanceAnalytics('class-1');
    expect(result.data).toBeDefined();
  });

  it('submitJustificationDirect posts justification form', async () => {
    const justification = { id: 'just-2', status: 'pending' };
    server.use(
      http.post('/api/v1/attendance/justifications', () =>
        HttpResponse.json({ data: justification, meta }),
      ),
    );
    const result = await attendanceService.submitJustificationDirect({
      student_id: 'student-1',
      class_id: 'class-1',
      date: '2025-01-07',
      reason: 'Illness',
    });
    expect(result.data.id).toBe('just-2');
  });

  it('reviewJustification posts review', async () => {
    server.use(
      http.post('/api/v1/attendance/justifications/just-1/review', () =>
        HttpResponse.json({ data: { id: 'just-1', status: 'approved' }, meta }),
      ),
    );
    const result = await attendanceService.reviewJustification('just-1', { decision: 'justified' });
    expect(result.data.status).toBe('approved');
  });

  it('checkThresholds posts threshold check', async () => {
    server.use(
      http.post('/api/v1/analytics/attendance/check-thresholds', () =>
        HttpResponse.json({ data: [], meta }),
      ),
    );
    const result = await attendanceService.checkThresholds();
    expect(result.data).toEqual([]);
  });
});

// ── gradebookService ──────────────────────────────────────────────────────────

describe('gradebookService', () => {
  const gradebookResponse = {
    class_id: 'class-1',
    class_name: 'Class 1',
    categories: [{ id: 'cat-1', name: 'Homework', weight: 0.3 }],
    assignments: [
      {
        assignment_id: 'assign-1',
        title: 'HW1',
        category_id: 'cat-1',
        total_points: 20,
        due_at: null,
      },
    ],
    rows: [
      {
        student_id: 'student-1',
        student_name: 'Alice',
        assignments: [{ assignment_id: 'assign-1', score: 18 }],
        weighted_average: 15,
      },
    ],
  };

  it('getClassGradebook returns mapped gradebook', async () => {
    server.use(
      http.get('/api/v1/gradebook/class-1/period-1', () =>
        HttpResponse.json({ data: gradebookResponse, meta }),
      ),
    );
    const result = await gradebookService.getClassGradebook('class-1', 'period-1');
    expect(result.data.class_id).toBe('class-1');
    expect(result.data.entries).toHaveLength(1);
  });

  it('getStudentGrades returns student grades', async () => {
    const transcriptResp = {
      student_id: 'student-1',
      student_name: 'Alice',
      periods: [
        {
          class_id: 'class-1',
          class_name: 'Class 1',
          period_id: 'period-1',
          period_label: 'T1',
          weighted_average: 15,
        },
      ],
    };
    server.use(
      http.get('/api/v1/gradebook/transcript/student-1', () =>
        HttpResponse.json({ data: transcriptResp, meta }),
      ),
    );
    const result = await gradebookService.getStudentGrades('student-1');
    expect(result.data.student_id).toBe('student-1');
  });

  it('updateGrades returns updated count', async () => {
    const result = await gradebookService.updateGrades({
      class_id: 'class-1',
      period_id: 'period-1',
      grades: [{ student_id: 'student-1', assessment_id: 'assign-1', value: 18 }],
    });
    expect(result.data.updated).toBe(1);
  });

  it('createCategory posts new category', async () => {
    server.use(
      http.post('/api/v1/gradebook/categories', () =>
        HttpResponse.json({ data: { id: 'cat-2', name: 'Quiz', weight: 0.2 }, meta }),
      ),
    );
    const result = await gradebookService.createCategory({
      name: 'Quiz',
      weight: 0.2,
      class_id: 'class-1',
      period_id: 'period-1',
    });
    expect(result.data.name).toBe('Quiz');
  });

  it('getCategories returns categories', async () => {
    server.use(
      http.get('/api/v1/gradebook/categories/class-1/period-1', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await gradebookService.getCategories('class-1', 'period-1');
    expect(result.data).toEqual([]);
  });

  it('computeGrades posts grade computation', async () => {
    server.use(
      http.post('/api/v1/gradebook/compute/class-1/period-1', () =>
        HttpResponse.json({
          data: {
            class_id: 'class-1',
            class_average: 14.5,
            pass_rate: 80,
            highest_average: 19,
            lowest_average: 8,
          },
          meta,
        }),
      ),
    );
    const result = await gradebookService.computeGrades('class-1', 'period-1');
    expect(result.data.class_average).toBe(14.5);
  });

  it('getTranscript returns transcript', async () => {
    server.use(
      http.get('/api/v1/gradebook/transcript/student-1', () =>
        HttpResponse.json({
          data: { student_id: 'student-1', student_name: 'Alice', periods: [] },
          meta,
        }),
      ),
    );
    const result = await gradebookService.getTranscript('student-1');
    expect(result.data).toBeDefined();
  });
});

// ── programsService ───────────────────────────────────────────────────────────

describe('programsService', () => {
  const program = {
    id: 'prog-1',
    school_id: 'school-1',
    code: 'PROG1',
    name: 'Program 1',
    level: 'primary',
    description: null,
    is_active: true,
    version_label: '1.0',
    effective_from: null,
    created_at: new Date().toISOString(),
    updated_at: null,
  };

  it('listPrograms returns programs', async () => {
    server.use(
      http.get('/api/v1/programs', () => HttpResponse.json({ data: [program], meta: listMeta })),
    );
    const result = await programsService.listPrograms();
    expect(result.data).toHaveLength(1);
  });

  it('getProgram returns single program', async () => {
    server.use(
      http.get('/api/v1/programs/prog-1', () => HttpResponse.json({ data: program, meta })),
    );
    const result = await programsService.getProgram('prog-1');
    expect(result.data.code).toBe('PROG1');
  });

  it('createProgram posts new program', async () => {
    server.use(http.post('/api/v1/programs', () => HttpResponse.json({ data: program, meta })));
    const result = await programsService.createProgram({ code: 'PROG1', name: 'Program 1' });
    expect(result.data.id).toBe('prog-1');
  });

  it('updateProgram patches program', async () => {
    server.use(
      http.patch('/api/v1/programs/prog-1', () =>
        HttpResponse.json({ data: { ...program, name: 'Updated' }, meta }),
      ),
    );
    const result = await programsService.updateProgram('prog-1', { name: 'Updated' });
    expect(result.data.name).toBe('Updated');
  });

  it('assignProgram posts program assignment', async () => {
    const event = {
      id: 'event-1',
      school_id: 'school-1',
      student_id: 'student-1',
      academic_year_id: 'year-1',
      period_id: null,
      from_program_id: null,
      to_program_id: 'prog-1',
      from_enrollment_id: null,
      to_enrollment_id: null,
      reason_code: 'INITIAL',
      reason_note: null,
      actor_user_id: null,
      occurred_at: new Date().toISOString(),
    };
    server.use(
      http.post('/api/v1/enrollments/enroll-1/program', () =>
        HttpResponse.json({ data: event, meta }),
      ),
    );
    const result = await programsService.assignProgram('enroll-1', {
      program_id: 'prog-1',
      reason_code: 'INITIAL',
    });
    expect(result.data.to_program_id).toBe('prog-1');
  });

  it('getProgramHistory returns history', async () => {
    server.use(
      http.get('/api/v1/students/student-1/program-history', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await programsService.getProgramHistory('student-1');
    expect(result.data).toEqual([]);
  });

  it('getAcademicTimeline returns timeline', async () => {
    server.use(
      http.get('/api/v1/students/student-1/academic-timeline', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await programsService.getAcademicTimeline('student-1');
    expect(result.data).toEqual([]);
  });

  it('getCurrentProgram returns current program', async () => {
    server.use(
      http.get('/api/v1/students/student-1/current-program', () =>
        HttpResponse.json({
          data: {
            student_id: 'student-1',
            academic_year_id: null,
            period_id: null,
            enrollment_id: null,
            program: null,
          },
          meta,
        }),
      ),
    );
    const result = await programsService.getCurrentProgram('student-1');
    expect(result.data.student_id).toBe('student-1');
  });

  it('listProgramVersions returns versions', async () => {
    server.use(
      http.get('/api/v1/programs/prog-1/versions', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await programsService.listProgramVersions('prog-1');
    expect(result.data).toEqual([]);
  });

  it('listProgramEquivalences returns equivalences', async () => {
    server.use(
      http.get('/api/v1/program-equivalences', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await programsService.listProgramEquivalences();
    expect(result.data).toEqual([]);
  });

  it('listEligibilityRules returns rules', async () => {
    server.use(
      http.get('/api/v1/eligibility/rules', () => HttpResponse.json({ data: [], meta: listMeta })),
    );
    const result = await programsService.listEligibilityRules();
    expect(result.data).toEqual([]);
  });

  it('checkEligibility returns eligibility check', async () => {
    server.use(
      http.get('/api/v1/students/student-1/eligibility', () =>
        HttpResponse.json({
          data: {
            student_id: 'student-1',
            target_program_id: 'prog-1',
            kind: 'PROMOTION',
            eligible: true,
            rules: [],
          },
          meta,
        }),
      ),
    );
    const result = await programsService.checkEligibility('student-1', 'PROMOTION', 'prog-1');
    expect(result.data.eligible).toBe(true);
  });
});

// ── skillsService ─────────────────────────────────────────────────────────────

describe('skillsService', () => {
  it('listDimensions returns skill dimensions', async () => {
    server.use(
      http.get('/api/v1/skills/dimensions', () =>
        HttpResponse.json({ data: [{ id: 'dim-1', name: 'Reading' }], meta: listMeta }),
      ),
    );
    const result = await skillsService.listDimensions();
    expect(result.data).toHaveLength(1);
  });

  it('createDimension posts new dimension', async () => {
    server.use(
      http.post('/api/v1/skills/dimensions', () =>
        HttpResponse.json({ data: { id: 'dim-2', name: 'Writing' }, meta }),
      ),
    );
    const result = await skillsService.createDimension({
      name: 'Writing',
      description: null,
      is_active: true,
    });
    expect(result.data.id).toBe('dim-2');
  });

  it('listMilestones returns milestones', async () => {
    server.use(
      http.get('/api/v1/skills/milestones', () => HttpResponse.json({ data: [], meta: listMeta })),
    );
    const result = await skillsService.listMilestones();
    expect(result.data).toEqual([]);
  });

  it('getStudentProgress returns student skill progress', async () => {
    server.use(
      http.get('/api/v1/skills/progress/student/student-1', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await skillsService.getStudentProgress('student-1', 'year-1');
    expect(result.data).toEqual([]);
  });

  it('getPassport returns skill passport', async () => {
    server.use(
      http.get('/api/v1/skills/passport/student-1', () =>
        HttpResponse.json({ data: { student_id: 'student-1', level: 2, dimensions: [] }, meta }),
      ),
    );
    const result = await skillsService.getPassport('student-1', 'year-1');
    expect(result.data).toBeDefined();
  });

  it('getClassAnalytics returns class analytics', async () => {
    server.use(
      http.get('/api/v1/skills/analytics/class/class-1', () =>
        HttpResponse.json({ data: { class_id: 'class-1', avg_level: 2 }, meta }),
      ),
    );
    const result = await skillsService.getClassAnalytics('class-1', 'year-1');
    expect(result.data).toBeDefined();
  });

  it('getSchoolAnalytics returns school analytics', async () => {
    server.use(
      http.get('/api/v1/skills/analytics/school', () =>
        HttpResponse.json({ data: { total_students: 100 }, meta }),
      ),
    );
    const result = await skillsService.getSchoolAnalytics('year-1');
    expect(result.data).toBeDefined();
  });

  it('getLeaderboard returns leaderboard', async () => {
    server.use(
      http.get('/api/v1/skills/leaderboard/class-1', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await skillsService.getLeaderboard('class-1', 'year-1');
    expect(result.data).toEqual([]);
  });
});

// ── resultsService ────────────────────────────────────────────────────────────

describe('resultsService', () => {
  it('listAssignmentResults returns results', async () => {
    server.use(http.get('/api/v1/results', () => HttpResponse.json({ data: [], meta: listMeta })));
    const result = await resultsService.listAssignmentResults({});
    expect(result.data).toEqual([]);
  });

  it('listQuizResults builds quiz results from quizzes', async () => {
    const quiz = {
      id: 'quiz-1',
      title: 'Q1',
      status: 'published',
      total_points: 20,
      school_id: null,
      created_by: 'user-1',
      description: null,
      subject: null,
      level_band: null,
      difficulty: null,
      time_limit_minutes: null,
      max_attempts: 1,
      shuffle_questions: false,
      question_count: 5,
    };
    server.use(
      http.get('/api/v1/quizzes', () => HttpResponse.json({ data: [quiz], meta: listMeta })),
    );
    const result = await resultsService.listQuizResults();
    expect(result.data).toHaveLength(1);
    expect(result.data[0].quiz_id).toBe('quiz-1');
  });
});

// ── progressService ───────────────────────────────────────────────────────────

describe('progressService', () => {
  const progressData = {
    data: {
      student_id: 'student-1',
      student_name: 'Alice',
      grade_trends: { labels: [], datasets: [] },
      content_completion: {
        summary: { total: 5, completed: 3, completion_rate: 60 },
        labels: [],
        datasets: [],
      },
      activity_scores: { labels: [], datasets: [] },
      attendance: {
        overview: {
          labels: [],
          datasets: [],
          summary: { total: 20, present: 18, attendance_rate: 90 },
        },
        trend: { labels: [], datasets: [] },
      },
      assessment_results: { labels: [], datasets: [] },
    },
  };

  it('getProgress with studentId calls student endpoint', async () => {
    server.use(
      http.get('/api/v1/progress/student/student-1', () =>
        HttpResponse.json({ data: progressData, meta }),
      ),
    );
    const result = await progressService.getProgress('student-1');
    expect(result.data).toBeDefined();
  });

  it('getProgress without studentId calls /progress/me', async () => {
    server.use(
      http.get('/api/v1/progress/me', () => HttpResponse.json({ data: progressData, meta })),
    );
    const result = await progressService.getProgress(null);
    expect(result.data).toBeDefined();
  });

  it('getChildrenOverview returns children data', async () => {
    server.use(
      http.get('/api/v1/progress/children', () =>
        HttpResponse.json({
          data: {
            data: {
              child_count: 2,
              children: [],
              charts: { comparison: { labels: [], datasets: [] } },
            },
          },
          meta,
        }),
      ),
    );
    const result = await progressService.getChildrenOverview();
    expect(result.data).toBeDefined();
  });

  it('getMyProgress returns my progress', async () => {
    server.use(
      http.get('/api/v1/progress/me', () => HttpResponse.json({ data: progressData, meta })),
    );
    const result = await progressService.getMyProgress();
    expect(result.data).toBeDefined();
  });
});
