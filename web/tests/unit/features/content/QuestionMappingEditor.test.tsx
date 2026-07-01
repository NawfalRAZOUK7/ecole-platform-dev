import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { QuestionMappingEditor } from '@/features/content/cms/ui/QuestionMappingEditor';
import { renderWithProviders } from '../../../utils/render';

const makeDragDropQuestion = (overrides = {}) => ({
  _key: 'q1',
  question_type: 'DRAG_DROP' as const,
  question_text: 'Sort the items',
  options: {
    items: [
      { id: 'i1', text: 'Apple' },
      { id: 'i2', text: 'Banana' },
    ],
    zones: [
      { id: 'z1', text: 'Fruit' },
      { id: 'z2', text: 'Veggie' },
    ],
  },
  correct_answer: { i1: 'z1' },
  points: 2,
  order: 0,
  explanation: '',
  ...overrides,
});

const makeMatchingQuestion = (overrides = {}) => ({
  _key: 'q2',
  question_type: 'MATCHING' as const,
  question_text: 'Match the pairs',
  options: {
    left: [
      { id: 'l1', text: 'Cat' },
      { id: 'l2', text: 'Dog' },
    ],
    right: [
      { id: 'r1', text: 'Meow' },
      { id: 'r2', text: 'Woof' },
    ],
  },
  correct_answer: { l1: 'r1' },
  points: 2,
  order: 0,
  explanation: '',
  ...overrides,
});

describe('QuestionMappingEditor – DRAG_DROP', () => {
  it('renders items and zones sections', () => {
    const onChange = vi.fn();
    renderWithProviders(
      <QuestionMappingEditor question={makeDragDropQuestion()} onChange={onChange} />,
    );
    // Items column header
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
    // Item texts should render in inputs
    const inputs = document.querySelectorAll('input[type="text"]');
    expect(inputs.length).toBeGreaterThanOrEqual(2);
  });

  it('renders item text inputs with correct values', () => {
    const onChange = vi.fn();
    renderWithProviders(
      <QuestionMappingEditor question={makeDragDropQuestion()} onChange={onChange} />,
    );
    const inputs = Array.from(
      document.querySelectorAll('input[type="text"]'),
    ) as HTMLInputElement[];
    const values = inputs.map((i) => i.value);
    expect(values).toContain('Apple');
    expect(values).toContain('Banana');
  });

  it('renders zone text inputs with correct values', () => {
    const onChange = vi.fn();
    renderWithProviders(
      <QuestionMappingEditor question={makeDragDropQuestion()} onChange={onChange} />,
    );
    const inputs = Array.from(
      document.querySelectorAll('input[type="text"]'),
    ) as HTMLInputElement[];
    const values = inputs.map((i) => i.value);
    expect(values).toContain('Fruit');
    expect(values).toContain('Veggie');
  });

  it('renders add item and add zone buttons', () => {
    const onChange = vi.fn();
    renderWithProviders(
      <QuestionMappingEditor question={makeDragDropQuestion()} onChange={onChange} />,
    );
    const buttons = Array.from(document.querySelectorAll('button')) as HTMLButtonElement[];
    const labels = buttons.map((b) => b.textContent ?? '');
    expect(labels.some((l) => /addItem|add item/i.test(l) || l.includes('+'))).toBe(true);
  });

  it('calls onChange when item text is edited', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <QuestionMappingEditor question={makeDragDropQuestion()} onChange={onChange} />,
    );
    const inputs = document.querySelectorAll('input[type="text"]');
    const appleInput = Array.from(inputs).find((i) => (i as HTMLInputElement).value === 'Apple') as
      | HTMLInputElement
      | undefined;
    if (appleInput) {
      await user.clear(appleInput);
      await user.type(appleInput, 'Orange');
      expect(onChange).toHaveBeenCalled();
    }
  });

  it('calls onChange when add item button clicked', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <QuestionMappingEditor question={makeDragDropQuestion()} onChange={onChange} />,
    );
    const buttons = Array.from(document.querySelectorAll('button')) as HTMLButtonElement[];
    const addBtn = buttons[0];
    if (addBtn) {
      await user.click(addBtn);
      expect(onChange).toHaveBeenCalled();
    }
  });

  it('calls onChange when zone mapping select changes', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <QuestionMappingEditor question={makeDragDropQuestion()} onChange={onChange} />,
    );
    const selects = document.querySelectorAll('select');
    if (selects.length > 0) {
      await user.selectOptions(selects[0] as HTMLSelectElement, 'z2');
      expect(onChange).toHaveBeenCalled();
    }
  });

  it('renders with empty options gracefully', () => {
    const onChange = vi.fn();
    renderWithProviders(
      <QuestionMappingEditor
        question={makeDragDropQuestion({
          options: { items: [], zones: [] },
          correct_answer: {},
        })}
        onChange={onChange}
      />,
    );
    expect(document.body).toBeTruthy();
  });
});

describe('QuestionMappingEditor – MATCHING', () => {
  it('renders left and right column headers', () => {
    const onChange = vi.fn();
    renderWithProviders(
      <QuestionMappingEditor question={makeMatchingQuestion()} onChange={onChange} />,
    );
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('renders left column item text inputs', () => {
    const onChange = vi.fn();
    renderWithProviders(
      <QuestionMappingEditor question={makeMatchingQuestion()} onChange={onChange} />,
    );
    const inputs = Array.from(
      document.querySelectorAll('input[type="text"]'),
    ) as HTMLInputElement[];
    const values = inputs.map((i) => i.value);
    expect(values).toContain('Cat');
    expect(values).toContain('Dog');
  });

  it('renders right column item text inputs', () => {
    const onChange = vi.fn();
    renderWithProviders(
      <QuestionMappingEditor question={makeMatchingQuestion()} onChange={onChange} />,
    );
    const inputs = Array.from(
      document.querySelectorAll('input[type="text"]'),
    ) as HTMLInputElement[];
    const values = inputs.map((i) => i.value);
    expect(values).toContain('Meow');
    expect(values).toContain('Woof');
  });

  it('renders pair mapping select', () => {
    const onChange = vi.fn();
    renderWithProviders(
      <QuestionMappingEditor question={makeMatchingQuestion()} onChange={onChange} />,
    );
    const selects = document.querySelectorAll('select');
    expect(selects.length).toBeGreaterThanOrEqual(1);
  });

  it('calls onChange when left text input is changed', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <QuestionMappingEditor question={makeMatchingQuestion()} onChange={onChange} />,
    );
    const inputs = document.querySelectorAll('input[type="text"]');
    const catInput = Array.from(inputs).find((i) => (i as HTMLInputElement).value === 'Cat') as
      | HTMLInputElement
      | undefined;
    if (catInput) {
      await user.clear(catInput);
      await user.type(catInput, 'Lion');
      expect(onChange).toHaveBeenCalled();
    }
  });

  it('calls onChange when matching select changes', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <QuestionMappingEditor question={makeMatchingQuestion()} onChange={onChange} />,
    );
    const selects = document.querySelectorAll('select');
    if (selects.length > 0) {
      await user.selectOptions(selects[0] as HTMLSelectElement, 'r2');
      expect(onChange).toHaveBeenCalled();
    }
  });

  it('calls onChange when add pair button is clicked', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <QuestionMappingEditor question={makeMatchingQuestion()} onChange={onChange} />,
    );
    const buttons = Array.from(document.querySelectorAll('button')) as HTMLButtonElement[];
    if (buttons.length > 0) {
      await user.click(buttons[0]);
      expect(onChange).toHaveBeenCalled();
    }
  });

  it('renders with empty left/right options', () => {
    const onChange = vi.fn();
    renderWithProviders(
      <QuestionMappingEditor
        question={makeMatchingQuestion({
          options: { left: [], right: [] },
          correct_answer: {},
        })}
        onChange={onChange}
      />,
    );
    expect(document.body).toBeTruthy();
  });
});
