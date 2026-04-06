export type FormMode = 'create' | 'edit' | 'view';

export interface FormState<T> {
  values: T;
  isDirty: boolean;
  isSubmitting: boolean;
  errors: Partial<Record<keyof T, string>>;
}
