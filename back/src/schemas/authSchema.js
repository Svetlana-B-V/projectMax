import { z } from 'zod';

export const loginByTelegramSchema = z.object({
  telegramId: z.number().int().positive(),
  name: z.string().min(1).optional(),
  avatarUrl: z.string().url().optional(),
});

export const linkEmailSchema = z.object({
  email: z.string().email(),
});