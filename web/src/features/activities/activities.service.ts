import { api } from '@/services/api/client';

export interface Activity {
  id: string;
  course_id: string;
  title: string;
  activity_type: string;
  difficulty: string | null;
  objective: string | null;
  config_json: Record<string, unknown> | null;
  created_at: string;
}

export interface ActivityFilters extends Record<string, string | number | undefined> {
  cursor?: string;
  limit?: number;
}

export const activitiesService = {
  list(filters: ActivityFilters = {}) {
    return api.list<Activity>('/activities', filters);
  },
};
