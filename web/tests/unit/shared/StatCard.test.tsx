import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { StatCard } from '@/shared/ui/StatCard';
import { renderWithProviders } from '../../utils/render';

describe('StatCard', () => {
  it('renders label and value', () => {
    renderWithProviders(<StatCard label="Total Users" value="150" />);
    expect(screen.getByText('Total Users')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
  });

  it('renders numeric value', () => {
    renderWithProviders(<StatCard label="Count" value={42} />);
    expect(screen.getByText('42')).toBeInTheDocument();
  });

  it('renders icon when provided', () => {
    renderWithProviders(<StatCard label="Revenue" value="$1,200" icon="💰" />);
    expect(screen.getByText('💰')).toBeInTheDocument();
  });

  it('renders upward trend with correct class and symbol', () => {
    const { container } = renderWithProviders(
      <StatCard label="Users" value="300" trend={{ direction: 'up', percentage: 12 }} />,
    );
    expect(screen.getByText('12%')).toBeInTheDocument();
    expect(screen.getByText('↗')).toBeInTheDocument();
    expect(container.querySelector('.stat-card__trend--up')).toBeInTheDocument();
  });

  it('renders downward trend with correct class and symbol', () => {
    const { container } = renderWithProviders(
      <StatCard label="Revenue" value="$800" trend={{ direction: 'down', percentage: 5 }} />,
    );
    expect(screen.getByText('5%')).toBeInTheDocument();
    expect(screen.getByText('↘')).toBeInTheDocument();
    expect(container.querySelector('.stat-card__trend--down')).toBeInTheDocument();
  });

  it('renders flat trend with arrow symbol', () => {
    renderWithProviders(
      <StatCard label="Active" value="100" trend={{ direction: 'flat', percentage: 0 }} />,
    );
    expect(screen.getByText('→')).toBeInTheDocument();
  });

  it('does not render trend when not provided', () => {
    const { container } = renderWithProviders(<StatCard label="Simple" value="10" />);
    expect(container.querySelector('.stat-card__trend')).not.toBeInTheDocument();
  });
});
