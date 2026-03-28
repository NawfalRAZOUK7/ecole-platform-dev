import { api } from '@/services/api/client';

export interface ContentItem {
  id: string;
  course_id: string;
  title: string;
  content_type: string;
  body_url: string | null;
  level_tag: string | null;
  language: string | null;
  sort_order: number;
  created_at: string;
}

export interface ContentFilters extends Record<string, string | number | undefined> {
  cursor?: string;
  search?: string;
  content_type?: string;
  level_tag?: string;
}

export const contentService = {
  listContentItems(params: ContentFilters) {
    return api.list<ContentItem>('/content-items', params);
  },
};
