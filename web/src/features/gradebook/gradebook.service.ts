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

export const gradebookService = {
  getClassGradebook(classId: string) {
    return api.get<GradebookGrid>(`/gradebook/class/${classId}`);
  },

  getStudentGrades(studentId: string) {
    return api.get<StudentGradeSummary>(`/gradebook/student/${studentId}`);
  },

  updateGrades(payload: BulkGradeUpdate) {
    return api.put<void>(`/gradebook/class/${payload.class_id}/grades`, {
      grades: payload.grades,
    });
  },

  getWeightedSummary(classId: string) {
    return api.get<GradebookWeightedSummary>(`/gradebook/class/${classId}/weighted-summary`);
  },

  exportGrades(classId: string, format: 'csv' | 'pdf') {
    return api.post<GradebookExportResponse>(`/gradebook/class/${classId}/export`, { format });
  },

  createCategory(payload: CreateCategoryPayload) {
    return api.post<GradebookCategory>('/gradebook/categories', payload);
  },

  getCategories(classId: string) {
    return api.get<GradebookCategory[]>('/gradebook/categories', { class_id: classId });
  },

  computeGrades(classId: string) {
    return api.post<GradebookWeightedSummary>(`/gradebook/class/${classId}/compute`);
  },

  getTranscript(studentId: string, academicYear?: string) {
    return api.get<GradebookTranscript>(`/gradebook/student/${studentId}/transcript`, {
      academic_year: academicYear,
    });
  },

  getPeriodGradebook(classId: string, period: string) {
    return api.get<GradebookGrid>(`/gradebook/class/${classId}/period/${period}`);
  },
};
