import { z } from 'zod';

export const createExpenseSchema = z.object({
  groupId: z.string().uuid(),
  payerId: z.string().uuid(),
  categoryId: z.string().uuid().optional(),
  amount: z.number().positive(),
  description: z.string().optional(),
  date: z.string().datetime().optional(),
  splits: z.array(z.object({
    userId: z.string().uuid(),
    amountOwed: z.number().nonnegative(),
  })).optional(),
});

export const updateExpenseSchema = z.object({
  amount: z.number().positive().optional(),
  description: z.string().optional(),
  categoryId: z.string().uuid().optional(),
  date: z.string().datetime().optional(),
}).refine(data => Object.keys(data).length > 0, { message: 'Нет данных для обновления' });