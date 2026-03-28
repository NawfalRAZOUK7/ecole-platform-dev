import { useMutation } from '@tanstack/react-query';
import { attendanceService, type ParentJustificationInput } from './attendance.service';

export function useSubmitJustification() {
  return useMutation({
    mutationFn: async (payload: ParentJustificationInput) => {
      await attendanceService.submitJustification(payload);
    },
  });
}
