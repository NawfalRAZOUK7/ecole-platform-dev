import userEvent from '@testing-library/user-event';
import { screen, waitFor } from '@testing-library/react';
import { delay, http } from 'msw';
import { describe, expect, it } from 'vitest';
import { SkillsOverviewPage } from '@/features/skills/SkillsOverviewPage';
import { renderWithProviders } from '../../utils/render';
import { apiErrorResponse, apiListResponse, server } from '../../utils/mocks';

const dimensions = [
  {
    id: 'dimension-1',
    code: 'autonomy',
    name_fr: 'Autonomie',
    name_ar: 'الاستقلالية',
    name_en: 'Autonomy',
    description_fr: 'Autonomy skills',
    display_order: 1,
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'dimension-2',
    code: 'collaboration',
    name_fr: 'Collaboration',
    name_ar: 'التعاون',
    name_en: 'Collaboration',
    description_fr: 'Collaboration skills',
    display_order: 2,
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
  },
];

const milestones = [
  {
    id: 'milestone-1',
    dimension_id: 'dimension-1',
    code: 'AUTO-1',
    name_fr: 'Autonomie 1',
    name_ar: 'استقلالية 1',
    level: 1,
    rule_config: {},
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'milestone-2',
    dimension_id: 'dimension-1',
    code: 'AUTO-2',
    name_fr: 'Autonomie 2',
    name_ar: 'استقلالية 2',
    level: 2,
    rule_config: {},
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'milestone-3',
    dimension_id: 'dimension-2',
    code: 'COLLAB-1',
    name_fr: 'Collaboration 1',
    name_ar: 'تعاون 1',
    level: 1,
    rule_config: {},
    is_active: true,
    created_at: '2026-01-01T00:00:00Z',
  },
];

const progressItems = [
  {
    id: 'progress-1',
    student_id: 'student-1',
    school_id: 'school-1',
    milestone_id: 'milestone-1',
    milestone_code: 'AUTO-1',
    dimension_id: 'dimension-1',
    dimension_code: 'autonomy',
    unlocked_at: '2026-04-01T00:00:00Z',
    current_value: 12,
    status: 'unlocked',
    evidence: null,
    academic_year_id: '2025-2026',
    created_at: '2026-04-01T00:00:00Z',
  },
  {
    id: 'progress-2',
    student_id: 'student-1',
    school_id: 'school-1',
    milestone_id: 'milestone-3',
    milestone_code: 'COLLAB-1',
    dimension_id: 'dimension-2',
    dimension_code: 'collaboration',
    unlocked_at: '2026-04-02T00:00:00Z',
    current_value: 9,
    status: 'unlocked',
    evidence: null,
    academic_year_id: '2025-2026',
    created_at: '2026-04-02T00:00:00Z',
  },
];

describe('SkillsOverviewPage', () => {
  it('loads skill dimensions and renders skills content', async () => {
    const user = userEvent.setup();

    server.use(
      http.get('/api/v1/skills/dimensions', () => apiListResponse(dimensions)),
      http.get('/api/v1/skills/milestones', () => apiListResponse(milestones)),
      http.get('/api/v1/skills/progress/student/:studentId', () => apiListResponse(progressItems))
    );

    renderWithProviders(<SkillsOverviewPage />, {
      user: { role: 'STD', id: 'student-1' },
    });

    expect(await screen.findByText('Skills Passport')).toBeInTheDocument();

    await user.type(screen.getAllByRole('textbox')[1], '2025-2026');

    expect(await screen.findByText('Autonomy')).toBeInTheDocument();
    expect(screen.getByText('Collaboration')).toBeInTheDocument();
    expect(screen.getByText('Dimension radar')).toBeInTheDocument();
  });

  it('shows an error banner when dimensions fail to load', async () => {
    server.use(
      http.get('/api/v1/skills/dimensions', () => apiErrorResponse('Unable to load skill dimensions')),
      http.get('/api/v1/skills/milestones', () => apiListResponse(milestones))
    );

    renderWithProviders(<SkillsOverviewPage />, {
      user: { role: 'STD', id: 'student-1' },
    });

    expect(await screen.findByText('Unable to load skill dimensions')).toBeInTheDocument();
  });

  it('shows a loading state while the skill catalog is loading', async () => {
    server.use(
      http.get('/api/v1/skills/dimensions', async () => {
        await delay(200);
        return apiListResponse(dimensions);
      }),
      http.get('/api/v1/skills/milestones', async () => {
        await delay(200);
        return apiListResponse(milestones);
      })
    );

    renderWithProviders(<SkillsOverviewPage />, {
      user: { role: 'STD', id: 'student-1' },
    });

    await waitFor(() => {
      expect(screen.getByRole('status', { name: 'Loading...' })).toBeInTheDocument();
    });
  });
});
