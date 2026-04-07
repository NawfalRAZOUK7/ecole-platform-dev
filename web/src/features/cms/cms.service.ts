import { getAccessToken, api } from '@/services/api/client';

export type QuestionType = 'MCQ' | 'TRUE_FALSE' | 'FILL_IN' | 'DRAG_DROP' | 'MATCHING';

export interface QuizQuestion {
  id?: string;
  question_type: string;
  question_text: string;
  options: unknown;
  correct_answer: unknown;
  points: number;
  order: number;
  explanation: string | null;
}

export interface Quiz {
  id: string;
  title: string;
  description: string | null;
  subject: string | null;
  level_band: string | null;
  difficulty: string | null;
  time_limit_minutes: number | null;
  max_attempts: number;
  shuffle_questions: boolean;
  status: string;
  questions?: QuizQuestion[];
}

export interface CmsContentItem {
  id: string;
  title: string;
  content_type: string;
  level_band: string | null;
  language: string | null;
  subject: string | null;
  description: string | null;
  thumbnail_path: string | null;
  origin: string;
  status: string;
  created_by: string | null;
  original_content_id: string | null;
}

export interface CmsLibraryItem {
  id: string;
  school_id: string | null;
  title: string;
  content_type: string;
  level_band: string | null;
  language: string | null;
  subject: string | null;
  description: string | null;
  origin: string;
  status: string;
}

export interface CmsContentFilters extends Record<string, string | number | undefined> {
  cursor?: string;
  content_type?: string;
  level_band?: string;
  subject?: string;
  language?: string;
  status?: string;
  origin?: string;
  search?: string;
}

export interface CmsLibraryFilters extends Record<string, string | number | undefined> {
  cursor?: string;
  limit?: number;
  content_type?: string;
  subject?: string;
  level_band?: string;
  origin?: string;
  status?: string;
}

export interface CmsSubmission {
  id: string;
  content_item_id: string;
  content_title: string | null;
  submitted_by: string;
  submitter_name: string | null;
  school_id: string;
  status: string;
  submitted_at: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
  promoted_content_id: string | null;
}

export interface CmsSubmissionFilters extends Record<string, string | number | undefined> {
  cursor?: string;
  status?: string;
  subject?: string;
  level_band?: string;
}

export interface CmsLibrarySubmission {
  id: string;
  content_item_id: string;
  content_title: string;
  status: string;
  submitted_at: string | null;
  review_notes: string | null;
  promoted_content_id: string | null;
}

export interface CmsClassContentItem {
  id: string;
  content_item_id: string;
  title: string;
  content_type: string;
  level_band: string | null;
  language: string | null;
  subject: string | null;
  description: string | null;
  assigned_at: string | null;
  teacher_notes: string | null;
}

export interface CmsContentStats {
  total_items: number;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
  by_subject: Record<string, number>;
  by_level: Record<string, number>;
  by_origin: Record<string, number>;
}

export interface CmsSubmissionStats {
  total_submissions: number;
  by_status: Record<string, number>;
  top_contributors: Array<{ submitter_name: string; count: number }>;
  avg_review_time_hours: number | null;
}

export interface CmsQuizStats {
  total_quizzes: number;
  published: number;
  total_attempts: number;
  avg_score: number | null;
}

function uploadAsset(contentId: string, file: File, onProgress?: (progress: number) => void) {
  return new Promise<void>((resolve, reject) => {
    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `/api/v1/content-items/${contentId}/assets`);
    const token = getAccessToken();
    if (token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    }

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
        return;
      }
      reject(new Error(`Upload failed: ${xhr.status}`));
    };

    xhr.onerror = () => reject(new Error('Network error'));
    xhr.send(formData);
  });
}

export const cmsService = {
  listQuizzes(params: Record<string, string | number | undefined> = {}) {
    return api.list<Quiz>('/quizzes', params);
  },

  getQuiz(quizId: string) {
    return api.get<Quiz>(`/quizzes/${quizId}`);
  },

  createQuiz(payload: Record<string, unknown>) {
    return api.post<{ id: string }>('/quizzes', payload);
  },

  updateQuiz(quizId: string, payload: Record<string, unknown>) {
    return api.put<void>(`/quizzes/${quizId}`, payload);
  },

  publishQuiz(quizId: string) {
    return api.post<void>(`/quizzes/${quizId}/publish`);
  },

  listContent(params: CmsContentFilters) {
    return api.list<CmsContentItem>('/cms/content', params);
  },

  async getContent(contentId: string) {
    const response = await api.list<CmsContentItem>('/cms/content', { limit: 200 });
    const item = response.data.find((content) => content.id === contentId);
    if (!item) {
      throw new Error('Content not found');
    }
    return item;
  },

  createContent(payload: Record<string, unknown>) {
    return api.post<{ id: string }>('/cms/content', payload);
  },

  updateContent(contentId: string, payload: Record<string, unknown>) {
    return api.put<void>(`/cms/content/${contentId}`, payload);
  },

  deleteContent(contentId: string) {
    return api.delete<void>(`/cms/content/${contentId}`);
  },

  listLibraryContent(params: CmsLibraryFilters) {
    return api.list<CmsLibraryItem>('/content/library', params);
  },

  assignLibraryContent(payload: { content_item_id: string; class_id: string; notes: string | null }) {
    return api.post<void>('/content/assign', payload);
  },

  removeLibraryAssignment(assignmentId: string) {
    return api.delete<void>(`/content/assign/${assignmentId}`);
  },

  submitLibraryContentForReview(contentItemId: string) {
    return api.post<void>('/content/submit-for-review', { content_item_id: contentItemId });
  },

  listLibrarySubmissions(params: CmsLibraryFilters) {
    return api.list<CmsLibrarySubmission>('/content/my-submissions', params);
  },

  listClassContent(classId: string) {
    return api.list<CmsClassContentItem>(`/classes/${classId}/content`);
  },

  uploadContentAsset(contentId: string, file: File, onProgress?: (progress: number) => void) {
    return uploadAsset(contentId, file, onProgress);
  },

  listSubmissions(params: CmsSubmissionFilters) {
    return api.list<CmsSubmission>('/cms/submissions', params);
  },

  reviewSubmission(submissionId: string, payload: Record<string, unknown>) {
    return api.post<void>(`/cms/submissions/${submissionId}/review`, payload);
  },

  async getAnalyticsSnapshot() {
    const [contentResponse, submissionsResponse, quizzesResponse] = await Promise.all([
      api.list<{
        id: string;
        status: string;
        content_type: string;
        subject: string | null;
        level_band: string | null;
        origin: string;
      }>('/cms/content', { limit: 200 }),
      api.list<{
        id: string;
        status: string;
        submitter_name: string | null;
        submitted_by: string;
        submitted_at: string;
        reviewed_at: string | null;
      }>('/cms/submissions', { limit: 200 }),
      api.list<{
        id: string;
        status: string;
      }>('/quizzes', { limit: 200 }),
    ]);

    const contentStats: CmsContentStats = {
      total_items: contentResponse.data.length,
      by_status: {},
      by_type: {},
      by_subject: {},
      by_level: {},
      by_origin: {},
    };
    for (const item of contentResponse.data) {
      contentStats.by_status[item.status] = (contentStats.by_status[item.status] || 0) + 1;
      contentStats.by_type[item.content_type] = (contentStats.by_type[item.content_type] || 0) + 1;
      if (item.subject) contentStats.by_subject[item.subject] = (contentStats.by_subject[item.subject] || 0) + 1;
      if (item.level_band) contentStats.by_level[item.level_band] = (contentStats.by_level[item.level_band] || 0) + 1;
      contentStats.by_origin[item.origin] = (contentStats.by_origin[item.origin] || 0) + 1;
    }

    const submissionStats: CmsSubmissionStats = {
      total_submissions: submissionsResponse.data.length,
      by_status: {},
      top_contributors: [],
      avg_review_time_hours: null,
    };
    const contributorMap: Record<string, { submitter_name: string; count: number }> = {};
    let totalReviewMs = 0;
    let reviewCount = 0;

    for (const item of submissionsResponse.data) {
      submissionStats.by_status[item.status] = (submissionStats.by_status[item.status] || 0) + 1;
      const key = item.submitted_by;
      if (!contributorMap[key]) {
        contributorMap[key] = {
          submitter_name: item.submitter_name || key,
          count: 0,
        };
      }
      contributorMap[key].count += 1;
      if (item.reviewed_at && item.submitted_at) {
        const diff = new Date(item.reviewed_at).getTime() - new Date(item.submitted_at).getTime();
        if (diff > 0) {
          totalReviewMs += diff;
          reviewCount += 1;
        }
      }
    }

    submissionStats.top_contributors = Object.values(contributorMap)
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
    if (reviewCount > 0) {
      submissionStats.avg_review_time_hours = Math.round((totalReviewMs / reviewCount / 3600000) * 10) / 10;
    }

    const quizStats: CmsQuizStats = {
      total_quizzes: quizzesResponse.data.length,
      published: quizzesResponse.data.filter((quiz) => quiz.status === 'published').length,
      total_attempts: 0,
      avg_score: null,
    };

    return {
      contentStats,
      submissionStats,
      quizStats,
    };
  },

  async getPendingSubmissionBadge() {
    const response = await api.list<{ id: string }>('/cms/submissions', {
      status: 'PENDING',
      limit: 1,
    });
    return response.meta.has_more ? 99 : response.data.length;
  },
};
