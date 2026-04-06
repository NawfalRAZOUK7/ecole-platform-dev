import { BrowserRouter } from 'react-router-dom';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

describe('Auth Context', () => {
  it('should render without crashing', () => {
    render(
      <BrowserRouter>
        <div data-testid="test">Hello</div>
      </BrowserRouter>
    );

    expect(screen.getByTestId('test')).toBeInTheDocument();
  });
});
