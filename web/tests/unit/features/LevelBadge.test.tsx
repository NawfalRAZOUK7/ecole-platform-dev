import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { LevelBadge } from '@/features/rewards/LevelBadge';
import { renderWithProviders } from '../../utils/render';

describe('LevelBadge', () => {
  it('renders level number inside the orb', () => {
    renderWithProviders(<LevelBadge level={5} xp={800} progress={60} />);
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('displays XP summary text', () => {
    renderWithProviders(<LevelBadge level={3} xp={320} progress={64} />);
    // The i18n key rewards.level.xpSummary with xp: 320
    expect(screen.getByText(/320/)).toBeInTheDocument();
  });

  it('shows clamped progress percentage', () => {
    renderWithProviders(<LevelBadge level={5} xp={800} progress={64} />);
    expect(screen.getByText('64%')).toBeInTheDocument();
  });

  it('clamps progress at 100% when over', () => {
    renderWithProviders(<LevelBadge level={5} xp={1200} progress={120} />);
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('clamps progress at 0% when negative', () => {
    renderWithProviders(<LevelBadge level={1} xp={0} progress={-10} />);
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('computes XP to next level correctly', () => {
    // xpThresholdForLevel(4) = 50 * 3 * 4 = 600
    // xpToNextLevel = 600 - 320 = 280
    renderWithProviders(<LevelBadge level={3} xp={320} progress={64} />);
    expect(screen.getByText('280')).toBeInTheDocument();
  });
});
