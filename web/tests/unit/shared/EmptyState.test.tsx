import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { EmptyState } from '@/shared/ui/EmptyState';
import { renderWithProviders } from '../../utils/render';

describe('EmptyState', () => {
  it('renders custom message', () => {
    renderWithProviders(<EmptyState message="There is nothing to display." />);
    expect(screen.getByText('There is nothing to display.')).toBeInTheDocument();
  });

  it('renders default inbox icon', () => {
    const { container } = renderWithProviders(<EmptyState />);
    expect(container.querySelector('.lucide-inbox')).toBeInTheDocument();
  });

  it('renders custom icon when provided', () => {
    renderWithProviders(<EmptyState icon="🔍" message="No results" />);
    expect(screen.getByText('🔍')).toBeInTheDocument();
  });

  it('has accessible status role', () => {
    renderWithProviders(<EmptyState />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});
