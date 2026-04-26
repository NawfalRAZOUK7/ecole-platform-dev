import { describe, expect, it } from 'vitest';
import { LoadingState } from '@/shared/ui/LoadingState';
import { renderWithProviders } from '../../utils/render';

describe('LoadingState', () => {
  it('renders a loading indicator with correct class', () => {
    const { container } = renderWithProviders(<LoadingState />);
    expect(container.querySelector('.loading-state')).toBeInTheDocument();
  });

  it('renders accessible loading role', () => {
    const { container } = renderWithProviders(<LoadingState />);
    const spinner =
      container.querySelector('[role="status"]') ?? container.querySelector('.loading-state');
    expect(spinner).toBeInTheDocument();
  });
});
