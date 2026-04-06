import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Badge } from '@/shared/ui/Badge';
import { renderWithProviders } from '../../utils/render';

describe('Badge', () => {
  it('renders all variants with the correct CSS classes', () => {
    renderWithProviders(
      <div>
        <Badge variant="success">success</Badge>
        <Badge variant="warning">warning</Badge>
        <Badge variant="error">error</Badge>
        <Badge variant="info">info</Badge>
        <Badge variant="neutral">neutral</Badge>
      </div>
    );

    expect(screen.getByText('success')).toHaveClass('badge', 'badge--success', 'badge--md');
    expect(screen.getByText('warning')).toHaveClass('badge', 'badge--warning', 'badge--md');
    expect(screen.getByText('error')).toHaveClass('badge', 'badge--error', 'badge--md');
    expect(screen.getByText('info')).toHaveClass('badge', 'badge--info', 'badge--md');
    expect(screen.getByText('neutral')).toHaveClass('badge', 'badge--neutral', 'badge--md');
  });
});
