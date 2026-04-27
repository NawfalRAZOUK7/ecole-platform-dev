/**
 * Shared review service — parent views child's sessions and posts comments.
 *
 * Phase B1: Interface de révision partagée parent-enfant.
 * API: GET/POST /api/v1/shared-reviews/{child_id}/sessions[/{session_id}]
 */

import { api } from '@/services/api/client';

export interface ReviewSession {
  id: string;
  type: 'quiz' | 'content' | 'writing' | 'activity';
  title: string;
  score?: number | null;
  max_score?: number;
  content_type?: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface ReviewComment {
  id: string;
  author_id: string;
  text: string;
  emoji: string | null;
  created_at: string;
}

export interface SessionDetail extends ReviewSession {
  text?: string;
  suggestion?: string;
  hints?: Record<string, unknown>;
  feedback?: Record<string, unknown>;
  comments: ReviewComment[];
}

export interface SessionsListResponse {
  child_id: string;
  sessions: ReviewSession[];
  total: number;
}

export const sharedReviewService = {
  /**
   * List child's recent learning sessions.
   */
  async listSessions(
    childId: string,
    params?: { limit?: number; offset?: number },
  ): Promise<SessionsListResponse> {
    const resp = await api.get<SessionsListResponse>(`/shared-reviews/${childId}/sessions`, params);
    return resp.data;
  },

  /**
   * Get detail of a specific session with comments.
   */
  async getSessionDetail(childId: string, sessionId: string): Promise<SessionDetail> {
    const resp = await api.get<SessionDetail>(`/shared-reviews/${childId}/sessions/${sessionId}`);
    return resp.data;
  },

  /**
   * Post a parent comment/encouragement on a session.
   */
  async addComment(
    childId: string,
    sessionId: string,
    body: { text: string; emoji?: string },
  ): Promise<ReviewComment> {
    const resp = await api.post<ReviewComment>(
      `/shared-reviews/${childId}/sessions/${sessionId}/comments`,
      body,
    );
    return resp.data;
  },
};
