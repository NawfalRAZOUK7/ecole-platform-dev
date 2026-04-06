import userEvent from '@testing-library/user-event';
import { screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { Pagination } from '@/shared/ui/Pagination';
import { renderWithProviders } from '../../utils/render';

describe('Pagination', () => {
  it('renders page numbers', () => {
    renderWithProviders(
      <Pagination currentPage={2} totalPages={4} pageSize={10} onPageChange={vi.fn()} />
    );

    expect(screen.getByRole('button', { name: '1' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '2' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '3' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '4' })).toBeInTheDocument();
  });

  it('disables previous on first page and next on last page', () => {
    const { rerender } = renderWithProviders(
      <Pagination currentPage={1} totalPages={4} pageSize={10} onPageChange={vi.fn()} />
    );

    expect(screen.getByRole('button', { name: /previous/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /next/i })).not.toBeDisabled();

    rerender(<Pagination currentPage={4} totalPages={4} pageSize={10} onPageChange={vi.fn()} />);

    expect(screen.getByRole('button', { name: /next/i })).toBeDisabled();
  });

  it('calls onPageChange with the correct page number', async () => {
    const user = userEvent.setup();
    const onPageChange = vi.fn();

    renderWithProviders(
      <Pagination currentPage={2} totalPages={4} pageSize={10} onPageChange={onPageChange} />
    );

    await user.click(screen.getByRole('button', { name: '3' }));
    await user.click(screen.getByRole('button', { name: /previous/i }));

    expect(onPageChange).toHaveBeenNthCalledWith(1, 3);
    expect(onPageChange).toHaveBeenNthCalledWith(2, 1);
  });
});
