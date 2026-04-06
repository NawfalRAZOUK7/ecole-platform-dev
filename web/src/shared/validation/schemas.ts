import { z as zod } from 'zod';

export const emailSchema = zod.string().email();
export const phoneSchema = zod.string().regex(/^\+?[0-9]{8,15}$/);
export const gradeSchema = zod.number().min(0).max(20);
export const currencySchema = zod.number().min(0).multipleOf(0.01);
export const dateSchema = zod.string().datetime();
export const requiredString = zod.string().min(1, 'required');
export const paginationSchema = zod.object({
  page: zod.number().min(1),
  pageSize: zod.number().min(1).max(100),
});

export type PaginationSchema = zod.infer<typeof paginationSchema>;
