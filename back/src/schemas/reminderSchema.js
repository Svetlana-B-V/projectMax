import { z } from 'zod';

export const updateReminderSchema = z.object({
  style: z.enum(['soft', 'neutral', 'playful']).optional(),
  enabled: z.boolean().optional(),
}).refine(data => Object.keys(data).length > 0, { message: 'Нет данных для обновления' });
