import { fireEvent, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { DataTable, type ColumnDef } from '@/shared/ui/DataTable';
import { renderWithProviders } from '../../utils/render';

interface TableRow {
  name: string;
  score: number;
}

const columns: ColumnDef<TableRow>[] = [
  { key: 'name', header: 'Name' },
  { key: 'score', header: 'Score' },
];

const data: TableRow[] = [
  { name: 'Charlie', score: 12 },
  { name: 'Alice', score: 18 },
  { name: 'Bob', score: 15 },
];

function getBodyRows() {
  return screen.getAllByRole('row').slice(1);
}

describe('DataTable', () => {
  it('renders columns and data correctly', () => {
    renderWithProviders(
      <DataTable columns={columns} data={data} loading={false} emptyMessage="app.empty" ariaLabel="Scores" />
    );

    expect(screen.getByRole('columnheader', { name: /name/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /score/i })).toBeInTheDocument();
    expect(screen.getByText('Charlie')).toBeInTheDocument();
    expect(screen.getByText('18')).toBeInTheDocument();
  });

  it('sorts by column click from asc to desc to none', () => {
    renderWithProviders(
      <DataTable columns={columns} data={data} loading={false} emptyMessage="app.empty" ariaLabel="Scores" />
    );

    const nameHeaderButton = screen.getByRole('button', { name: /name/i });

    fireEvent.click(nameHeaderButton);
    expect(getBodyRows().map((row) => within(row).getAllByRole('cell')[0].textContent)).toEqual(['Alice', 'Bob', 'Charlie']);

    fireEvent.click(nameHeaderButton);
    expect(getBodyRows().map((row) => within(row).getAllByRole('cell')[0].textContent)).toEqual(['Charlie', 'Bob', 'Alice']);

    fireEvent.click(nameHeaderButton);
    expect(getBodyRows().map((row) => within(row).getAllByRole('cell')[0].textContent)).toEqual(['Charlie', 'Alice', 'Bob']);
  });

  it('shows empty state when data is empty', () => {
    renderWithProviders(
      <DataTable columns={columns} data={[]} loading={false} emptyMessage="app.empty" />
    );

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows skeleton rows when loading', () => {
    const { container } = renderWithProviders(
      <DataTable columns={columns} data={[]} loading emptyMessage="app.empty" ariaLabel="Scores" />
    );

    expect(container.querySelectorAll('.skeleton--table-row')).toHaveLength(3);
  });

  it('calls onRowClick when a row is clicked', () => {
    const onRowClick = vi.fn();

    renderWithProviders(
      <DataTable columns={columns} data={data} loading={false} emptyMessage="app.empty" onRowClick={onRowClick} />
    );

    fireEvent.click(screen.getByText('Alice').closest('tr')!);

    expect(onRowClick).toHaveBeenCalledWith(data[1]);
  });
});
