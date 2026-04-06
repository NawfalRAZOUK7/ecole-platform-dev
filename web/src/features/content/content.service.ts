import { api } from '@/services/api/client';

export type ContentProgressStatus = 'not_started' | 'in_progress' | 'completed';

export interface ContentAsset {
  id: string;
  name?: string | null;
  mime_type?: string | null;
  download_url?: string | null;
  url?: string | null;
}

export interface ContentProgressRecord {
  id: string;
  student_id: string;
  content_item_id: string;
  status: ContentProgressStatus;
}

export interface ContentStudentAnalytics {
  students_started?: number | null;
  students_completed?: number | null;
  completion_rate?: number | null;
  average_score?: number | null;
  total_views?: number | null;
}

export interface ContentItem {
  id: string;
  course_id?: string | null;
  school_id?: string | null;
  title: string;
  description?: string | null;
  content_type: string;
  body_url?: string | null;
  embed_url?: string | null;
  external_url?: string | null;
  level_tag?: string | null;
  level_band?: string | null;
  language?: string | null;
  status?: string | null;
  sort_order?: number | null;
  created_at?: string | null;
  progress?: ContentProgressRecord | null;
  student_analytics?: ContentStudentAnalytics | null;
  assets?: ContentAsset[] | null;
}

export interface ContentFilters extends Record<string, string | number | undefined> {
  cursor?: string;
  search?: string;
  content_type?: string;
  level_band?: string;
}

export const contentService = {
  listContentItems(params: ContentFilters) {
    return api.list<ContentItem>('/content-items', params);
  },

  getContentItem(contentId: string) {
    return api.get<ContentItem>(`/content-items/${contentId}`);
  },

  updateProgress(contentId: string, status: ContentProgressStatus) {
    return api.post<ContentProgressRecord>(`/content-items/${contentId}/progress`, { status });
  },

  togglePublish(contentId: string, status: 'draft' | 'published') {
    return api.put<void>(`/cms/content/${contentId}`, { status });
  },

  updateOrdering(contentId: string, sortOrder: number) {
    return api.put<void>(`/cms/content/${contentId}`, { sort_order: sortOrder });
  },
};
