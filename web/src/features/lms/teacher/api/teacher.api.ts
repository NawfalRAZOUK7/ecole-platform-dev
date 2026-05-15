import { api, getAccessToken, getSchoolId } from '@/core/api/client';
import { directUpload, shouldUseDirect, type UploadKind } from '@/shared/lib/upload';
import { quizzesService, type QuizPayload } from '@/features/lms/quizzes/api/quizzes.api';

export interface TeacherCursorFilters extends Record<string, string | number | undefined> {
  cursor?: string;
  limit?: number;
}

export interface ClassOption {
  id: string;
  code: string;
  name: string;
}

export interface CourseItem {
  id: string;
  class_id: string;
  title: string;
  description: string | null;
  status: string;
}

export interface CourseOption {
  id: string;
  title: string;
  class_id: string;
}

export interface AssignmentItem {
  id: string;
  course_id: string;
  title: string;
  description: string | null;
  due_at: string | null;
  total_points: number;
}

export interface AssessmentItem {
  id: string;
  class_id: string;
  title: string;
  due_at: string | null;
  window_end: string | null;
  total_points: number;
  status: string;
}

export interface PeriodOption {
  id: string;
  label: string | null;
  date_start: string;
  date_end: string;
}

export interface StudentItem {
  id: string;
  full_name: string;
  email: string;
  enrollment_status?: string;
}

export interface StudentRow {
  student_id: string;
  student_name: string;
  grade_average: number;
  attendance_rate: number;
  content_completion_rate: number;
}

export interface ClassAverages {
  grade_average: number;
  attendance_rate: number;
  content_completion_rate: number;
}

export interface ChartDataset {
  label: string;
  data: number[];
}

export interface ClassProgressData {
  class_id: string;
  class_name: string;
  student_count: number;
  students: StudentRow[];
  class_averages: ClassAverages;
  charts: {
    grade_comparison: { labels: string[]; datasets: ChartDataset[] };
    attendance_comparison: { labels: string[]; datasets: ChartDataset[] };
  };
}

export interface ContentItem {
  id: string;
  school_id: string | null;
  title: string;
  content_type: string;
  level_band: string | null;
  language: string | null;
  subject: string | null;
  description: string | null;
  origin: string;
  status: string;
}

export interface ContentSubmissionItem {
  id: string;
  content_item_id: string;
  content_title: string;
  status: string;
  submitted_at: string | null;
  review_notes: string | null;
  promoted_content_id: string | null;
}

export interface Quiz {
  id: string;
  school_id: string | null;
  title: string;
  description: string | null;
  subject: string | null;
  level_band: string | null;
  difficulty: string | null;
  status: string;
  question_count: number;
  total_points: number;
  time_limit_minutes: number | null;
  max_attempts: number;
}

export interface QuestionInput {
  question_type: string;
  question_text: string;
  options: Record<string, unknown> | null;
  correct_answer: unknown;
  points: number;
  order: number;
  explanation: string;
}

export interface GradeInfo {
  score: number;
  feedback_text: string | null;
  published_at: string | null;
}

export interface SubmissionItem {
  id: string;
  assignment_id: string;
  assignment_title: string;
  assignment_total_points: number;
  student_id: string;
  student_name: string;
  status: string;
  submitted_at: string | null;
  grade: GradeInfo | null;
}

export interface TeacherCoursesFilters extends TeacherCursorFilters {
  class_id?: string;
}

export interface TeacherAssignmentsFilters extends TeacherCursorFilters {
  course_id?: string;
}

export interface TeacherAssessmentsFilters extends TeacherCursorFilters {
  class_id?: string;
  status?: string;
}

export interface TeacherContentFilters extends TeacherCursorFilters {
  content_type?: string;
  subject?: string;
  level_band?: string;
  origin?: string;
  status?: string;
}

export interface TeacherSubmissionFilters extends TeacherCursorFilters {
  assignment_id?: string;
  course_id?: string;
  status?: string;
}

export interface AttendanceRecordPayload {
  student_id: string;
  status: string;
  absence_reason: string | null;
}

export interface AttendanceSessionPayload {
  class_id: string;
  period_id: string;
  session_date: string;
  slot: string;
  records: AttendanceRecordPayload[];
}

export interface ContentUploadPayload {
  title: string;
  description?: string;
  content_type: string;
  level_band?: string;
  subject?: string;
  language: string;
  file: File;
}

export interface ClassDetail {
  id: string;
  code: string;
  name: string;
  academic_year_id: string;
  level?: string | null;
  grade?: string | null;
}

export interface ClassAssignmentPayload {
  class_id: string;
  [key: string]: unknown;
}

export interface AssessmentResultEntry {
  student_id: string;
  score: number;
  feedback?: string;
}

export interface AssessmentResultPayload {
  results: AssessmentResultEntry[];
}

export const teacherService = {
  listTeacherClasses() {
    return api.get<ClassOption[]>('/teacher/classes');
  },

  listTeacherPeriods() {
    return api.get<PeriodOption[]>('/teacher/periods');
  },

  listClassStudents(classId: string) {
    return api.get<StudentItem[]>(`/teacher/classes/${classId}/students`);
  },

  listCourses(params: TeacherCoursesFilters) {
    return api.list<CourseItem>('/courses', params);
  },

  createCourse(payload: Record<string, unknown>) {
    return api.post<void>('/courses', payload);
  },

  listAssignments(params: TeacherAssignmentsFilters) {
    return api.list<AssignmentItem>('/assignments', params);
  },

  createAssignment(payload: Record<string, unknown>) {
    return api.post<void>('/assignments', payload);
  },

  listAssessments(params: TeacherAssessmentsFilters) {
    return api.list<AssessmentItem>('/assessments', params);
  },

  createAssessment(payload: Record<string, unknown>) {
    return api.post<void>('/assessments', payload);
  },

  publishAssessment(assessmentId: string) {
    return api.post<void>(`/assessments/${assessmentId}/publish`);
  },

  createAttendanceSession(payload: AttendanceSessionPayload) {
    return api.post<void>('/attendance/sessions', payload);
  },

  getClassProgress(classId: string) {
    return api.get<{ data: ClassProgressData }>(`/progress/class/${classId}`);
  },

  listContentLibrary(params: TeacherContentFilters) {
    return api.list<ContentItem>('/content/library', params);
  },

  listAssignableClasses() {
    return api.list<ClassOption>('/teacher/classes');
  },

  assignContent(payload: { content_item_id: string; class_id: string; notes: string | null }) {
    return api.post<void>('/content/assign', payload);
  },

  submitContentForReview(contentId: string) {
    return api.post<void>('/content/submit-for-review', { content_item_id: contentId });
  },

  listMyContentSubmissions(params: TeacherContentFilters) {
    return api.list<ContentSubmissionItem>('/content/my-submissions', params);
  },

  async uploadContentItem(payload: ContentUploadPayload, onProgress?: (progress: number) => void) {
    const createResponse = await api.post<{ id: string }>('/cms/content', {
      title: payload.title.trim(),
      description: payload.description?.trim() || null,
      content_type: payload.content_type,
      level_band: payload.level_band || null,
      subject: payload.subject || null,
      language: payload.language,
      status: 'draft',
    });

    const contentItemId = createResponse.data.id;

    const kindMap: Record<string, UploadKind> = {
      video: 'content_asset',
      audio: 'content_asset',
      pdf: 'content_asset',
      interactive: 'content_asset',
      story: 'content_asset',
      coloring_book: 'content_asset',
    };
    const kind: UploadKind = kindMap[payload.content_type] ?? 'content_asset';

    if (shouldUseDirect(payload.file, kind)) {
      const schoolId = getSchoolId();
      if (!schoolId) throw new Error('No school context available');
      await directUpload({
        kind,
        scope: { school_id: schoolId, content_item_id: contentItemId },
        file: payload.file,
        onProgress,
      });
      return;
    }

    // Small files: legacy multipart path through the backend
    onProgress?.(15);
    const formData = new FormData();
    formData.append('file', payload.file);

    const token = getAccessToken();
    const uploadResponse = await fetch(`/api/v1/content-items/${contentItemId}/assets`, {
      method: 'POST',
      body: formData,
      credentials: 'include',
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });

    if (!uploadResponse.ok) {
      throw new Error('Upload failed');
    }

    onProgress?.(100);
  },

  listQuizzes(params: TeacherCursorFilters = {}) {
    return quizzesService.listQuizzes(params);
  },

  createQuiz(payload: Record<string, unknown>) {
    return quizzesService.createQuiz(payload as unknown as QuizPayload);
  },

  publishQuiz(quizId: string) {
    return quizzesService.publishQuiz(quizId);
  },

  listTeacherSubmissions(params: TeacherSubmissionFilters) {
    return api.list<SubmissionItem>('/teacher/submissions', params);
  },

  gradeSubmission(submissionId: string, payload: Record<string, unknown>) {
    return api.post<void>(`/submissions/${submissionId}/grade`, payload);
  },

  createClassAssignment(payload: ClassAssignmentPayload) {
    return api.post<{ id: string }>('/class-assignments', payload);
  },

  getClass(classId: string) {
    return api.get<ClassDetail>(`/classes/${classId}`);
  },

  submitAssessmentResults(assessmentId: string, payload: AssessmentResultPayload) {
    return api.post<void>(`/assessments/${assessmentId}/results`, payload);
  },
};
