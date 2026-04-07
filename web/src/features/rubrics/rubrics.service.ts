import { api } from '@/services/api/client';
import type {
  CreateRubricPayload,
  Rubric,
  RubricGradePayload,
  RubricGradeResult,
  RubricResultsResponse,
  UpdateRubricPayload,
} from './rubrics.types';

export const rubricsService = {
  listRubrics() {
    return api.get<Rubric[]>('/rubrics');
  },

  getRubric(id: string) {
    return api.get<Rubric>(`/rubrics/${id}`);
  },

  createRubric(payload: CreateRubricPayload) {
    return api.post<Rubric>('/rubrics', payload);
  },

  updateRubric(id: string, payload: UpdateRubricPayload) {
    return api.put<Rubric>(`/rubrics/${id}`, payload);
  },

  duplicateRubric(id: string) {
    return api.post<Rubric>(`/rubrics/${id}/duplicate`, {});
  },

  gradeRubric(payload: RubricGradePayload) {
    return api.post<RubricGradeResult>(`/rubrics/${payload.rubric_id}/grade`, payload);
  },

  getRubricResults(rubricId: string) {
    return api.get<RubricResultsResponse>(`/rubrics/${rubricId}/results`);
  },
};
