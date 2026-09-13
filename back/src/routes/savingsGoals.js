import { Router } from 'express';
import { createSavingsGoal, getSavingsGoals, contribute } from '../controllers/savingsGoalController.js';
import { validate } from '../middlewares/validate.js';
import { createSavingsGoalSchema, contributeSchema } from '../schemas/savingsGoalSchema.js';

const router = Router();

router.post('/', validate(createSavingsGoalSchema), createSavingsGoal);
router.get('/group/:groupId', getSavingsGoals);
router.post('/:goalId/contribute', validate(contributeSchema), contribute);

export default router;