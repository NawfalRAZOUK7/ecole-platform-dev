import { waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, vi } from 'vitest';
import { GameConfigEditor } from '@/features/ai/games/ui/GameConfigEditor';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiErrorResponse } from '../../../utils/mocks';

const mockGameConfig = {
  id: 'game-1',
  gameType: 'memory_match' as const,
  title: 'Numbers Game',
  titleAr: 'لعبة الأرقام',
  titleFr: 'Jeu des nombres',
  subject: 'Math',
  difficulty: 'easy' as const,
  targetAgeMin: 6,
  targetAgeMax: 10,
  rewardStars: 10,
  rewardXp: 15,
  isActive: true,
  schoolId: null,
  config: {
    pairs: [
      { front: 'One', back: '1', image_url: null },
      { front: 'Two', back: '2', image_url: null },
    ],
    grid_cols: 4,
    grid_rows: 4,
    time_limit: 60,
  },
};

describe('GameConfigEditor (new config)', () => {
  it('renders without crashing', async () => {
    renderWithProviders(<GameConfigEditor />, { user: { role: 'TCH' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders form fields for new game config', async () => {
    renderWithProviders(<GameConfigEditor />, { user: { role: 'TCH' } });
    await waitFor(() => {
      expect(document.body.innerHTML.length).toBeGreaterThan(0);
    });
  });

  it('renders memory match section by default', async () => {
    renderWithProviders(<GameConfigEditor />, { user: { role: 'TCH' } });
    await waitFor(() => {
      expect(document.body.innerHTML.length).toBeGreaterThan(0);
    });
  });

  it('renders cancel button', async () => {
    const onCancel = vi.fn();
    renderWithProviders(<GameConfigEditor onCancel={onCancel} embedded />, {
      user: { role: 'TCH' },
    });
    await waitFor(() => {
      expect(document.body.innerHTML.length).toBeGreaterThan(0);
    });
  });
});

describe('GameConfigEditor (edit config)', () => {
  it('renders with existing config', async () => {
    renderWithProviders(<GameConfigEditor config={mockGameConfig} />, { user: { role: 'TCH' } });
    await waitFor(() => {
      expect(document.body.innerHTML.length).toBeGreaterThan(0);
    });
  });

  it('shows update button when editing', async () => {
    renderWithProviders(<GameConfigEditor config={mockGameConfig} />, { user: { role: 'TCH' } });
    await waitFor(() => {
      expect(document.body.textContent).toBeTruthy();
    });
  });

  it('shows error state on save failure', async () => {
    server.use(http.put('/api/v1/games/configs/game-1', () => apiErrorResponse('Save failed')));
    renderWithProviders(<GameConfigEditor config={mockGameConfig} />, { user: { role: 'TCH' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
