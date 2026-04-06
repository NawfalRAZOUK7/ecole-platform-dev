import { useEffect } from 'react';
import { screen, waitFor } from '@testing-library/react';
import { FormProvider, useForm } from 'react-hook-form';
import { describe, expect, it } from 'vitest';
import { FormField } from '@/shared/ui/FormField';
import { renderWithProviders } from '../../utils/render';

interface FormValues {
  name: string;
}

function FormFieldHarness({ disabled = false, showError = false }: { disabled?: boolean; showError?: boolean }) {
  const methods = useForm<FormValues>({ defaultValues: { name: '' } });

  useEffect(() => {
    if (showError) {
      methods.setError('name', { type: 'manual', message: 'Required field' });
    }
  }, [methods, showError]);

  return (
    <FormProvider {...methods}>
      <FormField<FormValues> name="name" label="Name" disabled={disabled} />
    </FormProvider>
  );
}

describe('FormField', () => {
  it('renders label and input', () => {
    renderWithProviders(<FormFieldHarness />);

    expect(screen.getByLabelText('Name')).toBeInTheDocument();
  });

  it('shows validation error from react-hook-form', async () => {
    renderWithProviders(<FormFieldHarness showError />);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Required field');
    });
  });

  it('supports disabled state', () => {
    renderWithProviders(<FormFieldHarness disabled />);

    expect(screen.getByLabelText('Name')).toBeDisabled();
  });
});
