import { act, fireEvent, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { SearchInput } from '@/shared/ui/SearchInput';
import { renderWithProviders } from '../../utils/render';

describe('SearchInput', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('debounces onChange calls', async () => {
    const onChange = vi.fn();

    renderWithProviders(
      <SearchInput value="" onChange={onChange} placeholder="Search users" debounceMs={300} />
    );

    fireEvent.change(screen.getByRole('searchbox', { name: 'Search users' }), {
      target: { value: 'abc' },
    });
    expect(onChange).not.toHaveBeenCalled();

    act(() => {
      vi.advanceTimersByTime(300);
    });

    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith('abc');
  });

  it('clear button resets the value', () => {
    const onChange = vi.fn();

    renderWithProviders(
      <SearchInput value="initial" onChange={onChange} placeholder="Search users" debounceMs={300} />
    );

    fireEvent.click(screen.getByRole('button', { name: /clear/i }));

    expect(screen.getByRole('searchbox', { name: 'Search users' })).toHaveValue('');
    expect(onChange).toHaveBeenCalledWith('');
  });
});
