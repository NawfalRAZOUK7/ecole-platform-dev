import { screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { EventForm } from '@/features/communication/calendar/ui/EventForm';
import { renderWithProviders } from '../../../utils/render';

describe('EventForm', () => {
  it('renders nothing when isOpen is false', () => {
    const { container } = renderWithProviders(
      <EventForm
        availableClasses={[]}
        initialEvent={undefined}
        isOpen={false}
        onClose={vi.fn()}
        onSubmit={vi.fn()}
        userRole="ADM"
      />,
      { user: { role: 'ADM' } },
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders the create event form when isOpen is true', () => {
    renderWithProviders(
      <EventForm
        availableClasses={[]}
        initialEvent={undefined}
        isOpen={true}
        onClose={vi.fn()}
        onSubmit={vi.fn()}
        userRole="ADM"
      />,
      { user: { role: 'ADM' } },
    );
    expect(
      screen.getByText(/create event/i) || document.querySelector('.modal-overlay'),
    ).toBeTruthy();
  });

  it('renders title input fields', () => {
    renderWithProviders(
      <EventForm
        availableClasses={[]}
        initialEvent={undefined}
        isOpen={true}
        onClose={vi.fn()}
        onSubmit={vi.fn()}
        userRole="ADM"
      />,
      { user: { role: 'ADM' } },
    );
    expect(document.querySelector('input')).toBeTruthy();
  });

  it('renders cancel button', () => {
    renderWithProviders(
      <EventForm
        availableClasses={[]}
        initialEvent={undefined}
        isOpen={true}
        onClose={vi.fn()}
        onSubmit={vi.fn()}
        userRole="ADM"
      />,
      { user: { role: 'ADM' } },
    );
    expect(screen.getAllByText(/cancel/i).length).toBeGreaterThan(0);
  });
});
