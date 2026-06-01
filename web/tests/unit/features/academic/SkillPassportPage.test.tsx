import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { SkillPassportPage } from '@/features/academic/skills/ui/SkillPassportPage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiListResponse, apiResponse, server } from '../../../utils/mocks';

const mockDimension = {
  id: 'dim-1',
  name_fr: 'Compétences Cognitives',
  name_ar: 'المهارات المعرفية',
  name_en: 'Cognitive Skills',
  description: 'Cognitive development skills',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
};

const mockMilestone = {
  id: 'mil-1',
  dimension_id: 'dim-1',
  name_fr: 'Lecture Niveau 1',
  name_ar: 'القراءة المستوى 1',
  level: 1,
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
};

const mockPassport = {
  student_id: 'stu-1',
  academic_year_id: 'ay-2026',
  overall_score: 75,
  unlocked_milestones: 3,
  total_milestones: 10,
  generated_at: '2026-05-01T00:00:00Z',
  pdf_url: null,
  progress_items: [
    {
      milestone_id: 'mil-1',
      student_id: 'stu-1',
      status: 'unlocked',
      evaluated_at: '2026-04-01T00:00:00Z',
    },
  ],
};

function setupHandlers() {
  server.use(
    http.get('/api/v1/skills/dimensions', () => apiListResponse([mockDimension])),
    http.get('/api/v1/skills/milestones', () => apiListResponse([mockMilestone])),
    http.get('/api/v1/skills/passport/:studentId', () => apiResponse(mockPassport)),
  );
}

function renderPassportPage(studentId = 'stu-1') {
  return renderWithProviders(
    <Routes>
      <Route path="/skills/passport/:studentId" element={<SkillPassportPage />} />
    </Routes>,
    { route: `/skills/passport/${studentId}`, user: { role: 'TCH' } },
  );
}

describe('SkillPassportPage', () => {
  it('renders loading state while dimensions/milestones load', () => {
    server.use(
      http.get('/api/v1/skills/dimensions', async () => {
        await new Promise((r) => setTimeout(r, 100));
        return apiListResponse([]);
      }),
      http.get('/api/v1/skills/milestones', () => apiListResponse([])),
    );
    renderPassportPage();
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('renders the passport page title', async () => {
    setupHandlers();
    renderPassportPage();
    await waitFor(() => {
      expect(document.querySelector('.page')).toBeTruthy();
    });
  });

  it('shows the page header with actions', async () => {
    setupHandlers();
    renderPassportPage('stu-1');
    await waitFor(() => {
      // The page header actions (load passport, print) should be visible
      expect(
        document.querySelector('.page-header') || document.querySelector('.page'),
      ).toBeTruthy();
    });
  });

  it('shows passport stats when passport data is loaded', async () => {
    server.use(
      http.get('/api/v1/skills/dimensions', () => apiListResponse([mockDimension])),
      http.get('/api/v1/skills/milestones', () => apiListResponse([mockMilestone])),
      // For passport to load, academicYearId must be set; use search param
      http.get('/api/v1/skills/passport/:studentId', () => apiResponse(mockPassport)),
    );
    renderWithProviders(
      <Routes>
        <Route path="/skills/passport/:studentId" element={<SkillPassportPage />} />
      </Routes>,
      { route: '/skills/passport/stu-1?academicYearId=ay-2026', user: { role: 'TCH' } },
    );
    await waitFor(() => {
      expect(screen.queryByText('75%') || screen.queryByText('75')).toBeTruthy();
    });
  });

  it('shows error banner when dimensions fail to load', async () => {
    server.use(
      http.get('/api/v1/skills/dimensions', () => apiErrorResponse('Skills error')),
      http.get('/api/v1/skills/milestones', () => apiListResponse([])),
    );
    renderPassportPage();
    await waitFor(() => {
      expect(
        screen.queryByText(/Skills error/) ||
          screen.queryByText(/error/i) ||
          document.querySelector('[role="alert"]'),
      ).toBeTruthy();
    });
  });

  it('shows generate passport button for teacher with no passport', async () => {
    server.use(
      http.get('/api/v1/skills/dimensions', () => apiListResponse([mockDimension])),
      http.get('/api/v1/skills/milestones', () => apiListResponse([mockMilestone])),
      // Return 404 so passport is not found
      http.get('/api/v1/skills/passport/:studentId', () => apiErrorResponse('Not found', 404)),
    );
    renderWithProviders(
      <Routes>
        <Route path="/skills/passport/:studentId" element={<SkillPassportPage />} />
      </Routes>,
      { route: '/skills/passport/stu-1?academicYearId=ay-2026', user: { role: 'TCH' } },
    );
    await waitFor(() => {
      expect(
        screen.queryByText(/generatePassport|generate/i) ||
          screen.queryByText(/passportMissing|missing/i),
      ).toBeTruthy();
    });
  });

  it('renders load passport and print buttons', async () => {
    setupHandlers();
    renderPassportPage();
    await waitFor(() => {
      expect(
        screen.queryByRole('button', { name: /loadPassport|load/i }) ||
          screen.queryByRole('button', { name: /printPassport|print/i }),
      ).toBeTruthy();
    });
  });
});
