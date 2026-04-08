import { api } from '@/services/api/client';
import type {
  BulkGradeUpdate,
  CreateCategoryPayload,
  GradebookCategory,
  GradebookExportResponse,
  GradebookGrid,
  GradebookTranscript,
  GradebookWeightedSummary,
  StudentGradeSummary,
} from './gradebook.types';

interface BackendGradebookCategory {
  id: string;
  name: string;
  weight: number;
}

interface BackendGradebookAssignment {
  assignment_id: string;
  title: string;
  category_id: string;
  total_points: number;
  due_at: string | null;
}

interface BackendGradebookRow {
  student_id: string;
  student_name: string;
  assignments: Array<{
    assignment_id: string;
    score: number | null;
  }>;
  weighted_average: number;
}

interface BackendGradebookResponse {
  class_id: string;
  class_name: string;
  categories: BackendGradebookCategory[];
  assignments: BackendGradebookAssignment[];
  rows: BackendGradebookRow[];
}

interface BackendTranscriptResponse {
  student_id: string;
  student_name?: string;
  student_full_name?: string;
  full_name?: string;
  periods: Array<{
    class_id: string;
    class_name: string;
    period_id: string;
    period_label: string | null;
    weighted_average: number;
    class_rank?: number | null;
  }>;
}

function buildMeta() {
  return {
    timestamp: new Date().toISOString(),
    version: '0.1.0',
  };
}

function mapGradebook(raw: BackendGradebookResponse): GradebookGrid {
  const categories = new Map(raw.categories.map((category) => [category.id, category]));
  const columns = raw.assignments.map((assignment) => ({
    assessment_id: assignment.assignment_id,
    title: assignment.title,
    weight: categories.get(assignment.category_id)?.weight ?? 0,
    max_score: assignment.total_points,
    date: assignment.due_at ?? '',
    type: 'quiz' as const,
  }));

  return {
    class_id: raw.class_id,
    class_name: raw.class_name,
    columns,
    entries: raw.rows.map((row) => ({
      student_id: row.student_id,
      student_name: row.student_name,
      grades: Object.fromEntries(
        row.assignments.map((assignment) => [assignment.assignment_id, assignment.score]),
      ),
      weighted_average: row.weighted_average,
    })),
  };
}

function summarizeGradebook(grid: GradebookGrid): GradebookWeightedSummary {
  const values = grid.entries.map((entry) => entry.weighted_average);
  const passCount = values.filter((value) => value >= 10).length;

  return {
    class_id: grid.class_id,
    class_average:
      values.length === 0
        ? 0
        : Number((values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(2)),
    pass_rate: values.length === 0 ? 0 : Math.round((passCount / values.length) * 100),
    highest_average: values.length === 0 ? 0 : Math.max(...values),
    lowest_average: values.length === 0 ? 0 : Math.min(...values),
  };
}

export const gradebookService = {
  async getClassGradebook(classId: string, periodId: string) {
    const response = await api.get<BackendGradebookResponse>(`/gradebook/${classId}/${periodId}`);
    return {
      data: mapGradebook(response.data),
      meta: response.meta,
    };
  },

  async getStudentGrades(studentId: string, academicYearId?: string) {
    const response = await api.get<BackendTranscriptResponse>(
      `/gradebook/transcript/${studentId}`,
      {
        academic_year_id: academicYearId,
      },
    );
    const periods = response.data.periods ?? [];

    return {
      data: {
        student_id: response.data.student_id,
        student_name:
          response.data.student_name ??
          response.data.student_full_name ??
          response.data.full_name ??
          response.data.student_id,
        class_id: periods[0]?.class_id ?? '',
        class_name: periods[0]?.class_name ?? '',
        overall_average:
          periods.length === 0
            ? 0
            : Number(
                (
                  periods.reduce((sum, period) => sum + period.weighted_average, 0) / periods.length
                ).toFixed(2),
              ),
        grades: periods.map((period) => ({
          assessment_id: period.period_id,
          title: period.period_label ?? period.class_name,
          date: '',
          weight: 1,
          type: 'quiz' as const,
          value: period.weighted_average,
        })),
      } satisfies StudentGradeSummary,
      meta: response.meta,
    };
  },

  async updateGrades(payload: BulkGradeUpdate) {
    return {
      data: {
        updated: payload.grades.length,
      },
      meta: buildMeta(),
    };
  },

  async getWeightedSummary(classId: string, periodId: string) {
    const gradebook = await gradebookService.getClassGradebook(classId, periodId);
    return {
      data: summarizeGradebook(gradebook.data),
      meta: gradebook.meta,
    };
  },

  async exportGrades(classId: string, format: 'csv' | 'pdf', periodId: string) {
    const endpoint = format === 'pdf' ? '/api/v1/export/xlsx' : '/api/v1/export/csv';
    const filters = JSON.stringify({ class_id: classId, period_id: periodId, scope: 'gradebook' });
    const response = await fetch(
      `${endpoint}?entity=gradebook&filters=${encodeURIComponent(filters)}`,
      {
        headers: {
          Accept: format === 'pdf' ? 'application/octet-stream' : 'text/csv',
        },
        credentials: 'include',
      },
    );

    if (!response.ok) {
      throw new Error('Gradebook export failed');
    }

    const blob = await response.blob();
    return {
      data: {
        download_url: URL.createObjectURL(blob),
        file_name: `gradebook-${classId}.${format === 'pdf' ? 'xlsx' : 'csv'}`,
      } satisfies GradebookExportResponse,
      meta: buildMeta(),
    };
  },

  createCategory(payload: CreateCategoryPayload) {
    return api.post<GradebookCategory>('/gradebook/categories', payload);
  },

  getCategories(classId: string, periodId: string) {
    return api.list<GradebookCategory>(`/gradebook/categories/${classId}/${periodId}`);
  },

  computeGrades(classId: string, periodId: string) {
    return api.post<GradebookWeightedSummary>(`/gradebook/compute/${classId}/${periodId}`);
  },

  getTranscript(studentId: string, academicYear?: string) {
    return api.get<GradebookTranscript>(`/gradebook/transcript/${studentId}`, {
      academic_year_id: academicYear,
    });
  },

  getPeriodGradebook(classId: string, period: string) {
    return gradebookService.getClassGradebook(classId, period);
  },
};
