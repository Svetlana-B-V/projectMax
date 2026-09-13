import { z } from 'zod';

export const createGroupSchema = z.object({
  name: z.string().min(1),
  currency: z.string().default('RUB'),
});

export const joinGroupSchema = z.object({
  inviteCode: z.string().min(4),
});