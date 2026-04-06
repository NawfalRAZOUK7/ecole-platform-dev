import userEvent from '@testing-library/user-event';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ConfirmDialog } from '@/shared/ui/ConfirmDialog';
import { renderWithProviders } from '../../utils/render';

describe('ConfirmDialog', () => {
  it('opens and renders title and message', () => {
    renderWithProviders(
      <ConfirmDialog open title="Confirm action" message="Delete item?" onConfirm={vi.fn()} onCancel={vi.fn()} />
    );

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Confirm action')).toBeInTheDocument();
    expect(screen.getByText('Delete item?')).toBeInTheDocument();
  });

  it('calls onConfirm when confirm is clicked', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();

    renderWithProviders(
      <ConfirmDialog open title="Confirm action" message="Delete item?" onConfirm={onConfirm} onCancel={vi.fn()} />
    );

    await user.click(screen.getByRole('button', { name: /confirm/i }));

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('calls onCancel when cancel is clicked or Escape is pressed', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();

    const { rerender } = renderWithProviders(
      <ConfirmDialog open title="Confirm action" message="Delete item?" onConfirm={vi.fn()} onCancel={onCancel} />
    );

    await user.click(screen.getByRole('button', { name: /cancel/i }));
    expect(onCancel).toHaveBeenCalledTimes(1);

    rerender(
      <ConfirmDialog open title="Confirm action" message="Delete item?" onConfirm={vi.fn()} onCancel={onCancel} />
    );

    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onCancel).toHaveBeenCalledTimes(2);
  });

  it('traps focus within the dialog', async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <div>
        <button type="button">Outside</button>
        <ConfirmDialog open title="Confirm action" message="Delete item?" onConfirm={vi.fn()} onCancel={vi.fn()} />
      </div>
    );

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    const confirmButton = screen.getByRole('button', { name: /confirm/i });

    await waitFor(() => expect(cancelButton).toHaveFocus());
    await user.tab();
    expect(confirmButton).toHaveFocus();
    await user.tab();
    expect(cancelButton).toHaveFocus();
  });
});
