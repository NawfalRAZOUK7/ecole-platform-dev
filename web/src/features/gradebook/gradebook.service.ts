import { api } from '@/services/api/client';
import type {
  BulkGradeUpdate,
  GradebookExportResponse,
  GradebookGrid,
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
};
