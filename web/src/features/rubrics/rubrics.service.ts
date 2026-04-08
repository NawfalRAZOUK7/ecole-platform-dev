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

  async gradeRubric(payload: RubricGradePayload) {
    await api.post(
      `/submissions/${payload.assignment_id ?? payload.rubric_id}/grade-rubric`,
      payload.entries.map((entry) => ({
        criterion_id: entry.criterion_id,
        level_id: entry.level_id,
        points_awarded: entry.score,
        comment: null,
      })),
    );

    const totalScore = payload.entries.reduce((sum, entry) => sum + entry.score, 0);
    return {
      data: {
        student_id: payload.entries[0]?.student_id ?? '',
        rubric_id: payload.rubric_id,
        total_score: totalScore,
        max_score: totalScore,
        percentage: 100,
        entries: payload.entries,
      } satisfies RubricGradeResult,
      meta: {
        timestamp: new Date().toISOString(),
        version: '0.1.0',
      },
    };
  },

  getRubricResults(rubricId: string) {
    return api.get<RubricResultsResponse>(`/submissions/${rubricId}/rubric-results`);
  },
};
