import { api } from '@/services/api/client';

export interface Activity {
  id: string;
  course_id?: string | null;
  school_id?: string | null;
  title: string;
  activity_type?: string;
  type?: string;
  difficulty: string | null;
  objective?: string | null;
  pedagogical_objective?: string | null;
  description?: string | null;
  instructions?: string | null;
  config_json?: Record<string, unknown> | null;
  created_at?: string;
}

export interface ActivitySession {
  id: string;
  activity_id: string;
  student_id: string;
  student_name?: string | null;
  status: string;
  score?: number | null;
  attempt_no: number;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface ActivityParticipant {
  student_id: string;
  student_name: string;
  status?: string | null;
  attempts?: number | null;
  completed_sessions?: number | null;
  average_score?: number | null;
  last_activity_at?: string | null;
}

export interface ActivityGradingBucket {
  label: string;
  count: number;
}

export interface ActivityGradingSummary {
  average_score?: number | null;
  highest_score?: number | null;
  lowest_score?: number | null;
  completion_rate?: number | null;
  score_bands?: ActivityGradingBucket[] | null;
}

export interface ActivityDetail extends Activity {
  sessions?: ActivitySession[] | null;
  participants?: ActivityParticipant[] | null;
  grading?: ActivityGradingSummary | null;
}

export interface ActivityFilters extends Record<string, string | number | undefined> {
  cursor?: string;
  limit?: number;
  type?: string;
  difficulty?: string;
  search?: string;
}

export const activitiesService = {
  list(filters: ActivityFilters = {}) {
    return api.list<Activity>('/activities', filters);
  },

  getDetail(activityId: string) {
    return api.get<ActivityDetail>(`/activities/${activityId}`);
  },

  createSession(activityId: string) {
    return api.post<ActivitySession>('/activities/sessions', {
      activity_id: activityId,
    });
  },

  completeSession(sessionId: string, score?: number) {
    return api.post<ActivitySession>(`/activities/sessions/${sessionId}/complete`, {
      score,
    });
  },
};
