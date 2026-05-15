/**
 * React Query hook for the writing workspace.
 */

import { useMutation } from '@tanstack/react-query';
import { writingService, type WritingAttemptRequest } from '../api/writing.api';

export function useSubmitWriting() {
  return useMutation({
    mutationFn: (body: WritingAttemptRequest) => writingService.submitWriting(body),
  });
}
