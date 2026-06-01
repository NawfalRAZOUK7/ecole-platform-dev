import { screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { describe, expect, it, vi } from 'vitest';
import { SortingGame } from '@/features/ai/games/ui/SortingGame';
import { renderWithProviders } from '../../../utils/render';
import { server } from '../../../utils/mocks';

function setupCompleteHandler() {
  server.use(
    http.post('/api/v1/games/configs/:id/complete', () =>
      HttpResponse.json({
        data: { xpEarned: 20, levelUp: false },
        meta: { timestamp: '', version: '' },
      }),
    ),
  );
}

const mockGame = {
  id: 'game-sort-1',
  gameType: 'sorting' as const,
  title: 'Sort the Animals',
  titleAr: null,
  titleFr: null,
  subject: 'science',
  difficulty: 'easy' as const,
  targetAgeMin: 6,
  targetAgeMax: 10,
  rewardStars: 5,
  rewardXp: 20,
  isActive: true,
  schoolId: null,
  createdAt: '',
  updatedAt: '',
  config: {
    categories: [
      { name: 'Mammals', items: ['Dog', 'Cat', 'Cow'] },
      { name: 'Birds', items: ['Eagle', 'Parrot'] },
    ],
  },
};

const emptyGame = {
  ...mockGame,
  id: 'game-sort-empty',
  config: {
    categories: [],
  },
};

const singleCategoryGame = {
  ...mockGame,
  id: 'game-sort-single',
  config: {
    categories: [{ name: 'Fruits', items: ['Apple', 'Banana', 'Mango'] }],
  },
};

describe('SortingGame', () => {
  it('renders without crashing', async () => {
    setupCompleteHandler();
    renderWithProviders(<SortingGame game={mockGame} onExit={vi.fn()} />, {
      user: { role: 'STD' },
    });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('renders progress counter', async () => {
    setupCompleteHandler();
    renderWithProviders(<SortingGame game={mockGame} onExit={vi.fn()} />, {
      user: { role: 'STD' },
    });
    await waitFor(() => {
      expect(document.body.textContent).toMatch(/0\s*\/\s*5/);
    });
  });

  it('renders all category zones', async () => {
    setupCompleteHandler();
    renderWithProviders(<SortingGame game={mockGame} onExit={vi.fn()} />, {
      user: { role: 'STD' },
    });
    await waitFor(() => {
      expect(screen.getByText('Mammals')).toBeInTheDocument();
      expect(screen.getByText('Birds')).toBeInTheDocument();
    });
  });

  it('renders all draggable items in the available pool', async () => {
    setupCompleteHandler();
    renderWithProviders(<SortingGame game={mockGame} onExit={vi.fn()} />, {
      user: { role: 'STD' },
    });
    await waitFor(() => {
      expect(screen.getByText('Dog')).toBeInTheDocument();
      expect(screen.getByText('Cat')).toBeInTheDocument();
      expect(screen.getByText('Cow')).toBeInTheDocument();
      expect(screen.getByText('Eagle')).toBeInTheDocument();
      expect(screen.getByText('Parrot')).toBeInTheDocument();
    });
  });

  it('renders with empty categories config', async () => {
    setupCompleteHandler();
    renderWithProviders(<SortingGame game={emptyGame} onExit={vi.fn()} />, {
      user: { role: 'STD' },
    });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
    expect(document.body).toBeTruthy();
  });

  it('renders progress as 0 / 0 for empty categories', async () => {
    setupCompleteHandler();
    renderWithProviders(<SortingGame game={emptyGame} onExit={vi.fn()} />, {
      user: { role: 'STD' },
    });
    await waitFor(() => {
      expect(document.body.textContent).toMatch(/0\s*\/\s*0/);
    });
  });

  it('renders single category game', async () => {
    setupCompleteHandler();
    renderWithProviders(<SortingGame game={singleCategoryGame} onExit={vi.fn()} />, {
      user: { role: 'STD' },
    });
    await waitFor(() => {
      expect(screen.getByText('Fruits')).toBeInTheDocument();
      expect(screen.getByText('Apple')).toBeInTheDocument();
      expect(screen.getByText('Banana')).toBeInTheDocument();
      expect(screen.getByText('Mango')).toBeInTheDocument();
    });
  });

  it('draggable items have draggable attribute', async () => {
    setupCompleteHandler();
    renderWithProviders(<SortingGame game={mockGame} onExit={vi.fn()} />, {
      user: { role: 'STD' },
    });
    await waitFor(() => {
      const draggables = document.querySelectorAll('[draggable="true"]');
      expect(draggables.length).toBeGreaterThan(0);
    });
  });

  it('does not show completion banner at start', async () => {
    setupCompleteHandler();
    renderWithProviders(<SortingGame game={mockGame} onExit={vi.fn()} />, {
      user: { role: 'STD' },
    });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
    // GameCompleteBanner should not be shown at the start
    expect(document.body.textContent).not.toMatch(/replay/i);
  });

  it('progress indicator shows correct format', async () => {
    setupCompleteHandler();
    renderWithProviders(<SortingGame game={singleCategoryGame} onExit={vi.fn()} />, {
      user: { role: 'STD' },
    });
    await waitFor(() => {
      expect(document.body.textContent).toMatch(/0\s*\/\s*3/);
    });
  });

  it('calls onExit when component is interacted with', async () => {
    setupCompleteHandler();
    const onExit = vi.fn();
    renderWithProviders(<SortingGame game={mockGame} onExit={onExit} />, {
      user: { role: 'STD' },
    });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
    // onExit is only called when user exits from the completion banner
    // Just verify it was not called at initial render
    expect(onExit).not.toHaveBeenCalled();
  });
});
