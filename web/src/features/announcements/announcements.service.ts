import { api } from '@/services/api/client';

export interface Announcement {
  id: string;
  school_id: string;
  author_id: string;
  title: string;
  body: string;
  target_roles: string[];
  target_class_ids: string[];
  published_at: string | null;
  status: string;
  created_at: string;
  updated_at: string | null;
}

export interface AnnouncementFilters extends Record<string, string | number | undefined> {
  cursor?: string;
  limit?: number;
  status?: string;
}

export interface AnnouncementInput {
  title: string;
  body: string;
  target_roles: string[];
}

export const announcementsService = {
  list(filters: AnnouncementFilters) {
    return api.list<Announcement>('/announcements', filters);
  },

  create(payload: AnnouncementInput) {
    return api.post<void>('/announcements', payload);
  },

  update(announcementId: string, payload: AnnouncementInput) {
    return api.put<void>(`/announcements/${announcementId}`, payload);
  },

  publish(announcementId: string) {
    return api.post<void>(`/announcements/${announcementId}/publish`);
  },
};
