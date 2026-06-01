import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { questionBankService } from '@/features/lms/question-bank/api/question-bank.api';
import { quizzesService } from '@/features/lms/quizzes/api/quizzes.api';
import { rubricsService } from '@/features/lms/rubrics/api/rubrics.api';
import { studentService } from '@/features/lms/student/api/student.api';
import { writingService } from '@/features/lms/student/api/writing.api';
import { submissionsService } from '@/features/lms/submissions/api/submissions.api';
import { teacherService } from '@/features/lms/teacher/api/teacher.api';
import { server } from '../../utils/mocks';

const meta = { timestamp: new Date().toISOString(), version: '0.1.0' };
const listMeta = { ...meta, next_cursor: null, has_more: false };

// ── questionBankService ───────────────────────────────────────────────────────

describe('questionBankService', () => {
  it('createQuestion posts a question', async () => {
    const question = { id: 'q-1', type: 'MCQ', text: 'What is 2+2?', subject: 'Math' };
    server.use(
      http.post('/api/v1/question-bank', () => HttpResponse.json({ data: question, meta })),
    );
    const result = await questionBankService.createQuestion({
      type: 'MCQ',
      text: 'What is 2+2?',
      subject: 'Math',
      difficulty: 'easy',
      options: [],
      correct_answer: 'B',
    });
    expect(result.data.id).toBe('q-1');
  });

  it('listQuestions returns questions', async () => {
    server.use(
      http.get('/api/v1/question-bank', () =>
        HttpResponse.json({ data: { items: [], total: 0, page: 1, page_size: 20 }, meta }),
      ),
    );
    const result = await questionBankService.listQuestions({ subject: 'Math' });
    expect(result.data).toBeDefined();
  });

  it('importFromQuiz imports questions', async () => {
    server.use(
      http.post('/api/v1/question-bank/import/quiz-1', () =>
        HttpResponse.json({ data: { imported: 5 }, meta }),
      ),
    );
    const result = await questionBankService.importFromQuiz('quiz-1');
    expect(result.data).toBeDefined();
  });

  it('generateQuiz generates quiz from bank', async () => {
    server.use(
      http.post('/api/v1/question-bank/generate-quiz', () =>
        HttpResponse.json({ data: { quiz_id: 'quiz-new', questions: [] }, meta }),
      ),
    );
    const result = await questionBankService.generateQuiz({
      subject: 'Math',
      count: 5,
      difficulty: 'easy',
    });
    expect(result.data).toBeDefined();
  });

  it('getStats returns question bank stats', async () => {
    server.use(
      http.get('/api/v1/question-bank/stats', () =>
        HttpResponse.json({ data: { total: 100, by_subject: {}, by_difficulty: {} }, meta }),
      ),
    );
    const result = await questionBankService.getStats();
    expect(result.data.total).toBe(100);
  });
});

// ── quizzesService ────────────────────────────────────────────────────────────

describe('quizzesService', () => {
  const quiz = {
    id: 'quiz-1',
    school_id: null,
    created_by: 'user-1',
    title: 'Math Quiz',
    description: null,
    subject: 'Math',
    level_band: null,
    difficulty: null,
    time_limit_minutes: null,
    max_attempts: 3,
    shuffle_questions: false,
    status: 'draft',
    total_points: 20,
    question_count: 2,
  };

  it('createQuiz posts new quiz', async () => {
    server.use(
      http.post('/api/v1/quizzes', () => HttpResponse.json({ data: { id: 'quiz-1' }, meta })),
    );
    const result = await quizzesService.createQuiz({
      title: 'Math Quiz',
      max_attempts: 3,
      shuffle_questions: false,
      questions: [],
    });
    expect(result.data.id).toBe('quiz-1');
  });

  it('listQuizzes returns quizzes', async () => {
    server.use(
      http.get('/api/v1/quizzes', () => HttpResponse.json({ data: [quiz], meta: listMeta })),
    );
    const result = await quizzesService.listQuizzes();
    expect(result.data).toHaveLength(1);
  });

  it('getQuiz returns quiz detail', async () => {
    server.use(
      http.get('/api/v1/quizzes/quiz-1', () =>
        HttpResponse.json({ data: { ...quiz, questions: [] }, meta }),
      ),
    );
    const result = await quizzesService.getQuiz('quiz-1');
    expect(result.data.title).toBe('Math Quiz');
  });

  it('updateQuiz puts quiz', async () => {
    server.use(
      http.put('/api/v1/quizzes/quiz-1', () => HttpResponse.json({ data: undefined, meta })),
    );
    const result = await quizzesService.updateQuiz('quiz-1', { title: 'Updated Quiz' });
    expect(result).toBeDefined();
  });

  it('publishQuiz posts publish action', async () => {
    server.use(
      http.post('/api/v1/quizzes/quiz-1/publish', () =>
        HttpResponse.json({ data: { id: 'quiz-1', status: 'published' }, meta }),
      ),
    );
    const result = await quizzesService.publishQuiz('quiz-1');
    expect(result.data.status).toBe('published');
  });

  it('startAttempt posts attempt start', async () => {
    const attempt = {
      id: 'attempt-1',
      quiz_id: 'quiz-1',
      student_id: 'student-1',
      attempt_no: 1,
      started_at: new Date().toISOString(),
      completed_at: null,
      score: null,
      max_score: 20,
      status: 'in_progress',
    };
    server.use(
      http.post('/api/v1/quizzes/quiz-1/start', () => HttpResponse.json({ data: attempt, meta })),
    );
    const result = await quizzesService.startAttempt('quiz-1');
    expect(result.data.id).toBe('attempt-1');
  });

  it('respondToQuestion posts response', async () => {
    server.use(
      http.post('/api/v1/attempts/attempt-1/respond', () =>
        HttpResponse.json({
          data: {
            id: 'resp-1',
            attempt_id: 'attempt-1',
            question_id: 'q-1',
            answered_at: new Date().toISOString(),
          },
          meta,
        }),
      ),
    );
    const result = await quizzesService.respondToQuestion('attempt-1', {
      question_id: 'q-1',
      student_answer: 'A',
    });
    expect(result.data.id).toBe('resp-1');
  });

  it('submitAttempt posts submission', async () => {
    const attempt = {
      id: 'attempt-1',
      quiz_id: 'quiz-1',
      student_id: 'student-1',
      attempt_no: 1,
      started_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
      score: 18,
      max_score: 20,
      status: 'completed',
    };
    server.use(
      http.post('/api/v1/attempts/attempt-1/submit', () =>
        HttpResponse.json({ data: attempt, meta }),
      ),
    );
    const result = await quizzesService.submitAttempt('attempt-1');
    expect(result.data.status).toBe('completed');
  });

  it('getResults returns attempt results', async () => {
    server.use(
      http.get('/api/v1/attempts/attempt-1/results', () =>
        HttpResponse.json({ data: { attempt: { id: 'attempt-1' }, responses: [] }, meta }),
      ),
    );
    const result = await quizzesService.getResults('attempt-1');
    expect(result.data.responses).toEqual([]);
  });

  it('getAnalytics returns quiz analytics', async () => {
    server.use(
      http.get('/api/v1/quizzes/quiz-1/analytics', () =>
        HttpResponse.json({
          data: {
            quiz_id: 'quiz-1',
            title: 'Math Quiz',
            total_attempts: 5,
            completed_attempts: 4,
            average_score: 15,
            max_score_achieved: 20,
            min_score_achieved: 8,
            average_percentage: 75,
            question_stats: [],
          },
          meta,
        }),
      ),
    );
    const result = await quizzesService.getAnalytics('quiz-1');
    expect(result.data.total_attempts).toBe(5);
  });
});

// ── rubricsService ────────────────────────────────────────────────────────────

describe('rubricsService', () => {
  const rubric = { id: 'rub-1', name: 'Essay Rubric', criteria: [] };

  it('listRubrics returns rubrics', async () => {
    server.use(http.get('/api/v1/rubrics', () => HttpResponse.json({ data: [rubric], meta })));
    const result = await rubricsService.listRubrics();
    expect(result.data).toHaveLength(1);
  });

  it('getRubric returns single rubric', async () => {
    server.use(http.get('/api/v1/rubrics/rub-1', () => HttpResponse.json({ data: rubric, meta })));
    const result = await rubricsService.getRubric('rub-1');
    expect(result.data.id).toBe('rub-1');
  });

  it('createRubric posts new rubric', async () => {
    server.use(http.post('/api/v1/rubrics', () => HttpResponse.json({ data: rubric, meta })));
    const result = await rubricsService.createRubric({ name: 'Essay Rubric', criteria: [] });
    expect(result.data.name).toBe('Essay Rubric');
  });

  it('updateRubric puts rubric', async () => {
    server.use(
      http.put('/api/v1/rubrics/rub-1', () =>
        HttpResponse.json({ data: { ...rubric, name: 'Updated Rubric' }, meta }),
      ),
    );
    const result = await rubricsService.updateRubric('rub-1', { name: 'Updated Rubric' });
    expect(result.data.name).toBe('Updated Rubric');
  });

  it('duplicateRubric posts duplicate', async () => {
    server.use(
      http.post('/api/v1/rubrics/rub-1/duplicate', () =>
        HttpResponse.json({ data: { ...rubric, id: 'rub-2' }, meta }),
      ),
    );
    const result = await rubricsService.duplicateRubric('rub-1');
    expect(result.data.id).toBe('rub-2');
  });

  it('gradeRubric posts grade and returns result', async () => {
    server.use(
      http.post('/api/v1/submissions/assign-1/grade-rubric', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await rubricsService.gradeRubric({
      rubric_id: 'rub-1',
      assignment_id: 'assign-1',
      entries: [{ criterion_id: 'crit-1', level_id: 'lev-1', score: 10, student_id: 'student-1' }],
    });
    expect(result.data.total_score).toBe(10);
  });

  it('getRubricResults returns rubric results', async () => {
    server.use(
      http.get('/api/v1/submissions/rub-1/rubric-results', () =>
        HttpResponse.json({ data: { results: [] }, meta }),
      ),
    );
    const result = await rubricsService.getRubricResults('rub-1');
    expect(result.data).toBeDefined();
  });
});

// ── studentService ────────────────────────────────────────────────────────────

describe('studentService', () => {
  it('listPublishedQuizzes returns published quizzes', async () => {
    server.use(http.get('/api/v1/quizzes', () => HttpResponse.json({ data: [], meta: listMeta })));
    const result = await studentService.listPublishedQuizzes();
    expect(result.data).toEqual([]);
  });

  it('listStudentClasses returns enrollments', async () => {
    server.use(
      http.get('/api/v1/enrollments', () =>
        HttpResponse.json({
          data: [{ class_id: 'class-1', class_name: 'Class 1' }],
          meta: listMeta,
        }),
      ),
    );
    const result = await studentService.listStudentClasses();
    expect(result.data).toHaveLength(1);
  });

  it('listStudentWork returns work list', async () => {
    server.use(
      http.get('/api/v1/student-work', () =>
        HttpResponse.json({ data: { items: [], total: 0 }, meta }),
      ),
    );
    const result = await studentService.listStudentWork();
    expect(result.data.items).toEqual([]);
  });

  it('createEnrollment posts enrollment', async () => {
    server.use(
      http.post('/api/v1/enrollments', () =>
        HttpResponse.json({
          data: {
            id: 'enroll-1',
            student_id: 'student-1',
            class_id: 'class-1',
            period_id: 'period-1',
            school_id: 'school-1',
            status: 'active',
            program_id: null,
          },
          meta,
        }),
      ),
    );
    const result = await studentService.createEnrollment({
      student_id: 'student-1',
      class_id: 'class-1',
      period_id: 'period-1',
    });
    expect(result.data.id).toBe('enroll-1');
  });

  it('listClassContent returns class content', async () => {
    server.use(
      http.get('/api/v1/classes/class-1/content', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await studentService.listClassContent('class-1');
    expect(result.data).toEqual([]);
  });

  it('updateContentProgress posts progress update', async () => {
    server.use(
      http.post('/api/v1/content-items/ci-1/progress', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await studentService.updateContentProgress('ci-1', 'completed');
    expect(result).toBeDefined();
  });
});

// ── writingService ────────────────────────────────────────────────────────────

describe('writingService', () => {
  it('submitWriting posts writing attempt and returns feedback', async () => {
    const response = {
      id: 'write-1',
      text: 'My essay',
      feedback: {
        corrected_text: 'My essay.',
        suggestions: ['Add punctuation.'],
        score: 80,
        encouragement: 'Great job!',
      },
      created_at: new Date().toISOString(),
    };
    server.use(
      http.post('/api/v1/writing-attempts', () => HttpResponse.json({ data: response, meta })),
    );
    const result = await writingService.submitWriting({ text: 'My essay', language: 'fr' });
    expect(result.id).toBe('write-1');
    expect(result.feedback.score).toBe(80);
  });
});

// ── submissionsService ────────────────────────────────────────────────────────

describe('submissionsService', () => {
  it('listAssignments returns assignments', async () => {
    server.use(
      http.get('/api/v1/assignments', () => HttpResponse.json({ data: [], meta: listMeta })),
    );
    const result = await submissionsService.listAssignments();
    expect(result.data).toEqual([]);
  });

  it('createSubmission posts submission', async () => {
    server.use(
      http.post('/api/v1/submissions', () => HttpResponse.json({ data: { id: 'sub-1' }, meta })),
    );
    const result = await submissionsService.createSubmission('assign-1');
    expect(result.data.id).toBe('sub-1');
  });

  it('finalizeSubmission posts submission finalize', async () => {
    server.use(
      http.post('/api/v1/submissions/sub-1/submit', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await submissionsService.finalizeSubmission('sub-1');
    expect(result).toBeDefined();
  });

  it('overridePenalty posts penalty override', async () => {
    server.use(
      http.post('/api/v1/submissions/sub-1/override-penalty', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await submissionsService.overridePenalty('sub-1', {
      penalty_override: 0,
      reason: 'Extension granted',
    });
    expect(result).toBeDefined();
  });

  it('previewSubmission returns preview info', async () => {
    server.use(
      http.get('/api/v1/submissions/sub-1/preview', () =>
        HttpResponse.json({
          data: { preview_url: 'https://example.com/preview', status: 'ready' },
          meta,
        }),
      ),
    );
    const result = await submissionsService.previewSubmission('sub-1');
    expect(result.data.status).toBe('ready');
  });
});

// ── teacherService ────────────────────────────────────────────────────────────

describe('teacherService', () => {
  it('listTeacherClasses returns classes', async () => {
    server.use(
      http.get('/api/v1/teacher/classes', () =>
        HttpResponse.json({ data: [{ id: 'class-1', code: 'C1', name: 'Class 1' }], meta }),
      ),
    );
    const result = await teacherService.listTeacherClasses();
    expect(result.data).toHaveLength(1);
  });

  it('listTeacherPeriods returns periods', async () => {
    server.use(http.get('/api/v1/teacher/periods', () => HttpResponse.json({ data: [], meta })));
    const result = await teacherService.listTeacherPeriods();
    expect(result.data).toEqual([]);
  });

  it('listClassStudents returns students', async () => {
    server.use(
      http.get('/api/v1/teacher/classes/class-1/students', () =>
        HttpResponse.json({ data: [], meta }),
      ),
    );
    const result = await teacherService.listClassStudents('class-1');
    expect(result.data).toEqual([]);
  });

  it('listCourses returns courses', async () => {
    server.use(http.get('/api/v1/courses', () => HttpResponse.json({ data: [], meta: listMeta })));
    const result = await teacherService.listCourses({});
    expect(result.data).toEqual([]);
  });

  it('createCourse posts course', async () => {
    server.use(http.post('/api/v1/courses', () => HttpResponse.json({ data: undefined, meta })));
    const result = await teacherService.createCourse({ title: 'Math 101', class_id: 'class-1' });
    expect(result).toBeDefined();
  });

  it('listAssignments returns assignments', async () => {
    server.use(
      http.get('/api/v1/assignments', () => HttpResponse.json({ data: [], meta: listMeta })),
    );
    const result = await teacherService.listAssignments({});
    expect(result.data).toEqual([]);
  });

  it('createAssignment posts assignment', async () => {
    server.use(
      http.post('/api/v1/assignments', () => HttpResponse.json({ data: undefined, meta })),
    );
    const result = await teacherService.createAssignment({
      title: 'HW1',
      course_id: 'course-1',
      total_points: 20,
      due_at: null,
    });
    expect(result).toBeDefined();
  });

  it('listAssessments returns assessments', async () => {
    server.use(
      http.get('/api/v1/assessments', () => HttpResponse.json({ data: [], meta: listMeta })),
    );
    const result = await teacherService.listAssessments({});
    expect(result.data).toEqual([]);
  });

  it('createAssessment posts assessment', async () => {
    server.use(
      http.post('/api/v1/assessments', () => HttpResponse.json({ data: undefined, meta })),
    );
    const result = await teacherService.createAssessment({
      title: 'Midterm',
      class_id: 'class-1',
      total_points: 100,
    });
    expect(result).toBeDefined();
  });

  it('listTeacherSubmissions returns submissions', async () => {
    server.use(
      http.get('/api/v1/teacher/submissions', () =>
        HttpResponse.json({ data: [], meta: listMeta }),
      ),
    );
    const result = await teacherService.listTeacherSubmissions({});
    expect(result.data).toEqual([]);
  });

  it('gradeSubmission posts grade', async () => {
    server.use(
      http.post('/api/v1/submissions/sub-1/grade', () =>
        HttpResponse.json({ data: undefined, meta }),
      ),
    );
    const result = await teacherService.gradeSubmission('sub-1', {
      score: 18,
      feedback: 'Good work',
    });
    expect(result).toBeDefined();
  });

  it('getClass returns class detail', async () => {
    server.use(
      http.get('/api/v1/classes/class-1', () =>
        HttpResponse.json({
          data: { id: 'class-1', code: 'C1', name: 'Class 1', academic_year_id: 'year-1' },
          meta,
        }),
      ),
    );
    const result = await teacherService.getClass('class-1');
    expect(result.data.id).toBe('class-1');
  });
});
