import { Router } from 'express';
import { getMyReminders, updateMyReminders, ackReminder } from '../controllers/reminderController.js';
import { validate } from '../middlewares/validate.js';
import { updateReminderSchema } from '../schemas/reminderSchema.js';

const router = Router();

router.get('/', getMyReminders);
router.put('/', validate(updateReminderSchema), updateMyReminders);
router.post('/ack', ackReminder);

export default router;
