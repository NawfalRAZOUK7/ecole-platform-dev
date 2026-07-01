import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { StreakCard } from '@/features/ai/rewards/ui/StreakCard';
import { renderWithProviders } from '../../../utils/render';

describe('StreakCard', () => {
  it('renders current and longest streak values', () => {
    renderWithProviders(
      <StreakCard currentStreak={5} longestStreak={12} lastActivityAt="2026-04-25T10:00:00Z" />,
    );

    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
  });

  it('renders fire emoji', () => {
    renderWithProviders(<StreakCard currentStreak={3} longestStreak={7} lastActivityAt={null} />);

    expect(screen.getByText('🔥')).toBeInTheDocument();
  });

  it('renders zero streaks gracefully', () => {
    renderWithProviders(<StreakCard currentStreak={0} longestStreak={0} lastActivityAt={null} />);

    const zeros = screen.getAllByText('0');
    expect(zeros).toHaveLength(2);
  });

  it('shows formatted date for last activity', () => {
    renderWithProviders(
      <StreakCard currentStreak={5} longestStreak={12} lastActivityAt="2026-04-25T10:00:00Z" />,
    );

    // The formatDate output will contain the date — just check it's not "none"
    const lastActivitySection = screen.getByText(/2026|Apr|avril/i);
    expect(lastActivitySection).toBeInTheDocument();
  });
});
