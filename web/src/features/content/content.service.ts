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
  subject?: string | null;
  status?: string | null;
  sort_order?: number | null;
  page_count?: number | null;
  letter?: string | null;
  target_age_min?: number | null;
  target_age_max?: number | null;
  theme_color?: string | null;
  created_at?: string | null;
  progress?: ContentProgressRecord | null;
  student_analytics?: ContentStudentAnalytics | null;
  assets?: ContentAsset[] | null;
}

export interface ContentStoryPage {
  id: string;
  content_item_id: string;
  file_path: string;
  checksum?: string | null;
  mime_type?: string | null;
  file_size?: number | null;
  page_number: number | null;
  narration_text: string | null;
  has_activity: boolean;
  asset_type: string | null;
}

export interface ContentBadgeUnlock {
  code: string;
  title?: string | null;
  icon?: string | null;
}

export interface ContentRewardSnapshot {
  id: string;
  student_id?: string;
  stars: number;
  xp: number;
  level: number;
  streak_days?: number;
  badges?: string[];
  last_activity_at?: string | null;
  level_progress?: number;
}

export interface ContentCompleteResult {
  progress: ContentProgressRecord;
  reward: ContentRewardSnapshot;
  newly_earned_badges: ContentBadgeUnlock[];
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

  listStoryPages(contentId: string) {
    return api.list<ContentStoryPage>(`/content-items/${contentId}/pages`);
  },

  updateProgress(contentId: string, status: ContentProgressStatus) {
    return api.post<ContentProgressRecord>(`/content-items/${contentId}/progress`, { status });
  },

  completeContentItem(contentId: string, timeSpentSeconds?: number) {
    return api.post<ContentCompleteResult>(`/content-items/${contentId}/complete`, {
      time_spent_seconds: timeSpentSeconds,
    });
  },

  togglePublish(contentId: string, status: 'draft' | 'published') {
    return api.put<void>(`/cms/content/${contentId}`, { status });
  },

  updateOrdering(contentId: string, sortOrder: number) {
    return api.put<void>(`/cms/content/${contentId}`, { sort_order: sortOrder });
  },

  streamContent(contentItemId: string) {
    return api.get<{ stream_url: string; mime_type: string }>(
      `/content-items/${contentItemId}/stream`,
    );
  },

  getAsset(contentItemId: string, assetId: string) {
    return api.get<ContentAsset>(`/content-items/${contentItemId}/assets/${assetId}`);
  },

  deleteAsset(contentItemId: string, assetId: string) {
    return api.delete<void>(`/content-items/${contentItemId}/assets/${assetId}`);
  },
};
