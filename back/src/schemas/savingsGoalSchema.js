import { z } from 'zod';

export const createSavingsGoalSchema = z.object({
  groupId: z.string().uuid(),
  name: z.string().min(1),
  type: z.enum(['group', 'personal']).default('group'),
  targetAmount: z.number().positive(),
  deadline: z.string().datetime().optional(),
});

export const contributeSchema = z.object({
  amount: z.number().positive(),
  note: z.string().optional(),
});