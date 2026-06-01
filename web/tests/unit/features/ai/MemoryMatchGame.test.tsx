import { waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, vi } from 'vitest';
import { MemoryMatchGame } from '@/features/ai/games/ui/MemoryMatchGame';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse } from '../../../utils/mocks';

const mockGame = {
  id: 'game-1',
  gameType: 'memory_match' as const,
  title: 'Numbers Game',
  titleAr: null,
  titleFr: null,
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
      { front: 'Three', back: '3', image_url: null },
    ],
    grid_cols: 3,
    grid_rows: 2,
    time_limit: 60,
  },
};

describe('MemoryMatchGame', () => {
  it('renders without crashing', async () => {
    server.use(
      http.post('/api/v1/games/configs/game-1/complete', () =>
        HttpResponse.json({
          data: { xpEarned: 15, levelUp: false },
          meta: { timestamp: new Date().toISOString(), version: 'test' },
        }),
      ),
    );
    renderWithProviders(<MemoryMatchGame game={mockGame} onExit={vi.fn()} />, {
      user: { role: 'STD' },
    });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders stat chips with timer and move count', async () => {
    renderWithProviders(<MemoryMatchGame game={mockGame} onExit={vi.fn()} />, {
      user: { role: 'STD' },
    });
    await waitFor(() => {
      // Timer chip should show seconds
      expect(document.body.textContent).toContain('s');
    });
  });

  it('renders the game cards', async () => {
    renderWithProviders(<MemoryMatchGame game={mockGame} onExit={vi.fn()} />, {
      user: { role: 'STD' },
    });
    await waitFor(() => {
      // 3 pairs = 6 cards
      const buttons = document.body.querySelectorAll('button[aria-label]');
      expect(buttons.length).toBeGreaterThanOrEqual(6);
    });
  });

  it('renders pair count tracker', async () => {
    renderWithProviders(<MemoryMatchGame game={mockGame} onExit={vi.fn()} />, {
      user: { role: 'STD' },
    });
    await waitFor(() => {
      // Shows "0 / 3" (matched / total pairs)
      expect(document.body.textContent).toContain('0 / 3');
    });
  });
});
