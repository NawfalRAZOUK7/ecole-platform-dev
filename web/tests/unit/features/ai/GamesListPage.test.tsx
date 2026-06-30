import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';
import { GamesListPage } from '@/features/ai/games/ui/GamesListPage';
import { PERMISSIONS } from '@/shared/permissions';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiListResponse, server } from '../../../utils/mocks';

const mockGameConfig = {
  id: 'game-1',
  game_type: 'memory_match',
  title: 'Animals Memory Game',
  title_ar: null,
  title_fr: 'Jeu de Mémoire Animaux',
  subject: 'science',
  difficulty: 'easy',
  target_age_min: 6,
  target_age_max: 10,
  config: {},
  reward_stars: 3,
  reward_xp: 50,
  school_id: 'school-1',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

function setupHandlers() {
  server.use(http.get('/api/v1/games/configs', () => apiListResponse([mockGameConfig])));
}

describe('GamesListPage', () => {
  it('renders loading state initially', () => {
    server.use(
      http.get('/api/v1/games/configs', async () => {
        await new Promise((r) => setTimeout(r, 100));
        return apiListResponse([]);
      }),
    );
    renderWithProviders(<GamesListPage />, {
      user: { role: 'TCH', permissions: [PERMISSIONS.GAME_CONFIG_MANAGE] },
    });
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('renders game list for teacher role', async () => {
    setupHandlers();
    renderWithProviders(<GamesListPage />, { user: { role: 'TCH' } });
    expect(await screen.findByText('Animals Memory Game')).toBeInTheDocument();
  });

  it('shows create game button for teacher role', async () => {
    setupHandlers();
    renderWithProviders(<GamesListPage />, {
      user: { role: 'TCH', permissions: [PERMISSIONS.GAME_CONFIG_MANAGE] },
    });
    await waitFor(() => {
      expect(
        screen.queryByRole('button', { name: /create/i }) || screen.queryByText(/createGame/i),
      ).toBeTruthy();
    });
  });

  it('does not show create game button for student role', async () => {
    setupHandlers();
    renderWithProviders(<GamesListPage />, { user: { role: 'STD' } });
    await waitFor(() => {
      expect(document.querySelector('.page')).toBeTruthy();
    });
    expect(screen.queryByRole('button', { name: /create/i })).toBeNull();
  });

  it('shows empty state when no games', async () => {
    server.use(http.get('/api/v1/games/configs', () => apiListResponse([])));
    renderWithProviders(<GamesListPage />, { user: { role: 'TCH' } });
    await waitFor(() => {
      expect(
        document.querySelector('.empty-state') ||
          screen.queryByText(/empty/i) ||
          screen.queryByText(/🎮/),
      ).toBeTruthy();
    });
  });

  it('shows error banner when games fail to load', async () => {
    server.use(http.get('/api/v1/games/configs', () => apiErrorResponse('Failed to load games')));
    renderWithProviders(<GamesListPage />, { user: { role: 'TCH' } });
    expect(await screen.findByText(/Failed to load games/)).toBeInTheDocument();
  });

  it('renders filter controls', async () => {
    setupHandlers();
    renderWithProviders(<GamesListPage />, { user: { role: 'TCH' } });
    await waitFor(() => {
      // Filter selects should be present
      const selects = document.querySelectorAll('select.filter-select');
      expect(selects.length).toBeGreaterThan(0);
    });
  });
});
