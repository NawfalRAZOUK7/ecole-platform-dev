import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http } from 'msw';
import { describe, expect, it, vi } from 'vitest';
import { StudentHomePage } from '@/features/user/student/ui/StudentHomePage';
import { renderWithProviders } from '../../../utils/render';
import { apiResponse, server } from '../../../utils/mocks';

const mockRewards = {
  id: 'reward-1',
  student_id: 'student-1',
  stars: 42,
  xp: 320,
  level: 3,
  streak_days: 5,
  longest_streak: 12,
  badges: ['first_login', 'quiz_master', 'streak_7'],
  last_activity_at: '2026-04-25T10:00:00Z',
  level_progress: 64,
};

function setupRewardsHandler(data = mockRewards) {
  server.use(http.get('/api/v1/rewards/me', () => apiResponse(data)));
}

describe('StudentHomePage', () => {
  it('renders greeting with user first name', async () => {
    setupRewardsHandler();
    renderWithProviders(<StudentHomePage />, {
      user: { role: 'STD', full_name: 'Amine Razouk' },
    });

    expect(await screen.findByText(/Amine/)).toBeInTheDocument();
  });

  it('displays XP, stars, streak, and level stats', async () => {
    setupRewardsHandler();
    renderWithProviders(<StudentHomePage />, {
      user: { role: 'STD', full_name: 'Amine' },
    });

    expect(await screen.findByText('320')).toBeInTheDocument(); // XP
    expect(screen.getByText('42')).toBeInTheDocument(); // Stars
    expect(screen.getByText('5')).toBeInTheDocument(); // Streak
    expect(screen.getByText('3')).toBeInTheDocument(); // Level
  });

  it('renders level progress bar with correct aria attributes', async () => {
    setupRewardsHandler();
    renderWithProviders(<StudentHomePage />, {
      user: { role: 'STD', full_name: 'Amine' },
    });

    const progressBar = await screen.findByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveAttribute('aria-valuemin', '0');
    expect(progressBar).toHaveAttribute('aria-valuemax', '100');
  });

  it('renders CTA buttons for learning, quiz, and writing', async () => {
    setupRewardsHandler();
    renderWithProviders(<StudentHomePage />, {
      user: { role: 'STD', full_name: 'Amine' },
    });

    await screen.findByText('320'); // Wait for data load

    expect(screen.getByText('Start Learning')).toBeInTheDocument();
    expect(screen.getByText('Take a Quiz')).toBeInTheDocument();
    expect(screen.getByText('Write a Story')).toBeInTheDocument();
  });

  it('renders badge chips when student has badges', async () => {
    setupRewardsHandler();
    renderWithProviders(<StudentHomePage />, {
      user: { role: 'STD', full_name: 'Amine' },
    });

    await screen.findByText('320'); // Wait for data load

    expect(screen.getByText(/first_login/)).toBeInTheDocument();
    expect(screen.getByText(/quiz_master/)).toBeInTheDocument();
    expect(screen.getByText(/streak_7/)).toBeInTheDocument();
  });

  it('does not render badge section when no badges', async () => {
    setupRewardsHandler({ ...mockRewards, badges: [] });
    renderWithProviders(<StudentHomePage />, {
      user: { role: 'STD', full_name: 'Amine' },
    });

    await screen.findByText('320'); // Wait for data load

    expect(screen.queryByText('My Badges')).not.toBeInTheDocument();
  });

  it('renders quick links section with navigation buttons', async () => {
    setupRewardsHandler();
    renderWithProviders(<StudentHomePage />, {
      user: { role: 'STD', full_name: 'Amine' },
    });

    await screen.findByText('320'); // Wait for data load

    expect(screen.getByRole('button', { name: /progress/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /rewards/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /announcements/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /calendar/i })).toBeInTheDocument();
  });

  it('shows loading state while rewards are loading', () => {
    server.use(
      http.get('/api/v1/rewards/me', () => {
        return new Promise(() => {}); // Never resolves
      }),
    );

    const { container } = renderWithProviders(<StudentHomePage />, {
      user: { role: 'STD', full_name: 'Amine' },
    });

    // LoadingState component should be visible
    expect(container.querySelector('.loading-state')).toBeInTheDocument();
  });
});
