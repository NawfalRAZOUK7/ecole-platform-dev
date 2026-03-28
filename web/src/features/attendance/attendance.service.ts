import { api } from '@/services/api/client';

export interface ParentJustificationInput {
  attendance_record_id: string;
  reason: string;
}

export const attendanceService = {
  submitJustification(payload: ParentJustificationInput) {
    return api.post<void>('/attendance/justifications', payload);
  },
};
