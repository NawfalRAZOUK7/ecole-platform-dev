import { api } from '@/core/api/client';
import type { ProgressData, ChildrenResponse } from '../model/types';

export const progressApi = {
  getProgress(studentId?: string | null) {
    return api.get<ProgressData>(studentId ? `/progress/student/${studentId}` : '/progress/me');
  },

  getChildrenOverview() {
    return api.get<ChildrenResponse>('/progress/children');
  },

  getStudentProgress(studentId: string) {
    return api.get<ProgressData>(`/progress/student/${studentId}`);
  },

  getMyProgress() {
    return api.get<ProgressData>('/progress/me');
  },
};
