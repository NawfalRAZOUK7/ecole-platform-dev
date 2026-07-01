import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';
import { http, HttpResponse } from 'msw';
import { server } from '../../../utils/mocks';
import { describe, it, expect } from 'vitest';
import {
  useCmsQuizzes,
  useCmsQuiz,
  useCreateCmsQuiz,
  useUpdateCmsQuiz,
  usePublishCmsQuiz,
  useCmsContent,
  useCmsContentItem,
  useCmsLibraryContent,
  useCmsClassContent,
  useCreateCmsContent,
  useUpdateCmsContent,
  useCmsLibrarySubmissions,
  useCmsAssignLibraryContent,
  useCmsUnassignLibraryContent,
  useCmsSubmitLibraryContentForReview,
} from '@/features/content/cms/model/useCms';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) =>
    QueryClientProvider({ client: queryClient, children });
}

function apiListResponse<T>(data: T[]) {
  return HttpResponse.json({
    data,
    meta: {
      next_cursor: null,
      has_more: false,
      timestamp: new Date().toISOString(),
      version: 'test',
    },
  });
}

function apiResponse<T>(data: T) {
  return HttpResponse.json({
    data,
    meta: { timestamp: new Date().toISOString(), version: 'test' },
  });
}

function apiError(status = 500) {
  return HttpResponse.json(
    {
      error: { code: 'ERR', message: 'fail', category: 'system', retryable: false, timestamp: '' },
    },
    { status },
  );
}

const mockQuiz = {
  id: 'quiz-1',
  title: 'Quiz de mathématiques',
  description: 'Test des bases',
  subject: 'math',
  level_band: 'cp',
  difficulty: 'easy',
  time_limit_minutes: 30,
  max_attempts: 3,
  shuffle_questions: false,
  status: 'draft',
  questions: [],
};

const mockContentItem = {
  id: 'content-1',
  title: 'Les animaux de la ferme',
  content_type: 'story',
  level_band: 'cp',
  language: 'fr',
  subject: 'science',
  description: 'Une histoire sur les animaux',
  page_count: 10,
  letter: null,
  target_age_min: 5,
  target_age_max: 7,
  theme_color: '#FF6B6B',
  thumbnail_path: null,
  origin: 'school',
  status: 'draft',
  created_by: 'user-1',
  original_content_id: null,
};

const mockLibraryItem = {
  id: 'lib-1',
  school_id: 'sch-1',
  title: 'Livre de bibliothèque',
  content_type: 'book',
  level_band: 'ce1',
  language: 'fr',
  subject: 'literature',
  description: null,
  page_count: 25,
  letter: null,
  target_age_min: 6,
  target_age_max: 8,
  theme_color: null,
  origin: 'platform',
  status: 'published',
};

describe('useCmsQuizzes', () => {
  it('returns quizzes on success', async () => {
    server.use(http.get('/api/v1/quizzes', () => apiListResponse([mockQuiz])));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCmsQuizzes(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([mockQuiz]);
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/quizzes', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCmsQuizzes(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useCmsQuiz', () => {
  it('returns quiz detail', async () => {
    server.use(http.get('/api/v1/quizzes/quiz-1', () => apiResponse(mockQuiz)));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCmsQuiz('quiz-1'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockQuiz);
  });

  it('does not fetch when quizId is null', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCmsQuiz(null), { wrapper });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useCreateCmsQuiz', () => {
  it('creates a quiz', async () => {
    server.use(
      http.post('/api/v1/quizzes', () => apiResponse(mockQuiz)),
      http.get('/api/v1/quizzes', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCreateCmsQuiz(), { wrapper });
    act(() => result.current.mutate({ title: 'New Quiz', subject: 'math' }));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockQuiz);
  });

  it('handles error', async () => {
    server.use(http.post('/api/v1/quizzes', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCreateCmsQuiz(), { wrapper });
    act(() => result.current.mutate({ title: 'Test' }));
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useUpdateCmsQuiz', () => {
  it('updates a quiz', async () => {
    server.use(
      http.put('/api/v1/quizzes/quiz-1', () => apiResponse(null)),
      http.get('/api/v1/quizzes', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useUpdateCmsQuiz(), { wrapper });
    act(() => result.current.mutate({ quizId: 'quiz-1', payload: { title: 'Updated Quiz' } }));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('usePublishCmsQuiz', () => {
  it('publishes a quiz', async () => {
    server.use(
      http.post('/api/v1/quizzes/quiz-1/publish', () => apiResponse(null)),
      http.get('/api/v1/quizzes', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => usePublishCmsQuiz(), { wrapper });
    act(() => result.current.mutate('quiz-1'));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useCmsContent', () => {
  it('returns CMS content items', async () => {
    server.use(http.get('/api/v1/cms/content', () => apiListResponse([mockContentItem])));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCmsContent({}), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.pages[0].data).toEqual([mockContentItem]);
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/cms/content', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCmsContent({}), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });

  it('accepts content filters', async () => {
    server.use(http.get('/api/v1/cms/content', () => apiListResponse([mockContentItem])));
    const wrapper = createWrapper();
    const { result } = renderHook(
      () => useCmsContent({ content_type: 'story', level_band: 'cp' }),
      { wrapper },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('supports pagination with hasNextPage', async () => {
    server.use(
      http.get('/api/v1/cms/content', () =>
        HttpResponse.json({
          data: [mockContentItem],
          meta: {
            next_cursor: 'c2',
            has_more: true,
            timestamp: new Date().toISOString(),
            version: 'test',
          },
        }),
      ),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCmsContent({}), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.hasNextPage).toBe(true);
  });
});

describe('useCmsContentItem', () => {
  it('returns content item by searching the list', async () => {
    server.use(http.get('/api/v1/cms/content', () => apiListResponse([mockContentItem])));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCmsContentItem('content-1'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('does not fetch when contentId is null', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCmsContentItem(null), { wrapper });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useCmsLibraryContent', () => {
  it('returns library content on success', async () => {
    server.use(http.get('/api/v1/content/library', () => apiListResponse([mockLibraryItem])));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCmsLibraryContent({}), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.pages[0].data).toEqual([mockLibraryItem]);
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/content/library', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCmsLibraryContent({}), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useCmsClassContent', () => {
  it('returns class content on success', async () => {
    const classContent = [
      {
        id: 'cc-1',
        content_item_id: 'content-1',
        title: 'Story',
        content_type: 'story',
        level_band: 'cp',
        language: 'fr',
        subject: 'science',
        description: null,
        page_count: null,
        letter: null,
        target_age_min: null,
        target_age_max: null,
        theme_color: null,
        assigned_at: '2026-01-01',
        teacher_notes: null,
      },
    ];
    server.use(http.get('/api/v1/classes/cls-1/content', () => apiListResponse(classContent)));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCmsClassContent('cls-1'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(classContent);
  });

  it('does not fetch when classId is null', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCmsClassContent(null), { wrapper });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useCreateCmsContent', () => {
  it('creates content', async () => {
    server.use(
      http.post('/api/v1/cms/content', () => apiResponse({ id: 'new-content-1' })),
      http.get('/api/v1/cms/content', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCreateCmsContent(), { wrapper });
    act(() => result.current.mutate({ title: 'New Story', content_type: 'story' }));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual({ id: 'new-content-1' });
  });

  it('handles error', async () => {
    server.use(http.post('/api/v1/cms/content', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCreateCmsContent(), { wrapper });
    act(() => result.current.mutate({ title: 'Test' }));
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useUpdateCmsContent', () => {
  it('updates content', async () => {
    server.use(
      http.put('/api/v1/cms/content/content-1', () => apiResponse(null)),
      http.get('/api/v1/cms/content', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useUpdateCmsContent(), { wrapper });
    act(() => result.current.mutate({ contentId: 'content-1', payload: { title: 'Updated' } }));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useCmsLibrarySubmissions', () => {
  it('returns library submissions on success', async () => {
    const mockSubmission = {
      id: 'sub-1',
      content_item_id: 'content-1',
      content_title: 'My Story',
      status: 'pending',
      submitted_at: '2026-09-01T00:00:00Z',
      review_notes: null,
      promoted_content_id: null,
    };
    server.use(http.get('/api/v1/content/my-submissions', () => apiListResponse([mockSubmission])));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCmsLibrarySubmissions({}), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.pages[0].data).toEqual([mockSubmission]);
  });
});

describe('useCmsAssignLibraryContent', () => {
  it('assigns library content to class', async () => {
    server.use(
      http.post('/api/v1/content/assign', () => apiResponse(null)),
      http.get('/api/v1/content/library', () => apiListResponse([])),
      http.get('/api/v1/classes/cls-1/content', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCmsAssignLibraryContent(), { wrapper });
    act(() => result.current.mutate({ content_item_id: 'lib-1', class_id: 'cls-1', notes: null }));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useCmsUnassignLibraryContent', () => {
  it('removes library assignment', async () => {
    server.use(
      http.delete('/api/v1/content/assign/assign-1', () => apiResponse(null)),
      http.get('/api/v1/cms/content', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCmsUnassignLibraryContent(), { wrapper });
    act(() => result.current.mutate('assign-1'));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useCmsSubmitLibraryContentForReview', () => {
  it('submits content for review', async () => {
    server.use(
      http.post('/api/v1/content/submit-for-review', () => apiResponse(null)),
      http.get('/api/v1/content/library', () => apiListResponse([])),
      http.get('/api/v1/content/my-submissions', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCmsSubmitLibraryContentForReview(), { wrapper });
    act(() => result.current.mutate('content-1'));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBe('content-1');
  });
});
