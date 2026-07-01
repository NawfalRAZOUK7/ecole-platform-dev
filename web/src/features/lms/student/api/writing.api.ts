/**
 * Writing workspace service — calls the AI writing-attempts endpoint.
 *
 * API: POST /api/v1/writing-attempts
 * Sends student text, receives AI feedback (corrections, suggestions).
 */

import { api } from '@/core/api/client';

export interface WritingAttemptRequest {
  text: string;
  language?: string;
  writing_type?: string;
}

export interface WritingFeedback {
  corrected_text: string;
  suggestions: string[];
  score: number | null;
  encouragement: string;
}

export interface WritingAttemptResponse {
  id: string;
  text: string;
  feedback: WritingFeedback;
  created_at: string;
}

export const writingService = {
  /**
   * Submit a writing attempt and get AI feedback.
   */
  async submitWriting(body: WritingAttemptRequest): Promise<WritingAttemptResponse> {
    const resp = await api.post<WritingAttemptResponse>('/writing-attempts', body);
    return resp.data;
  },
};
