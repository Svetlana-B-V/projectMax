import { Router } from 'express';
import { getMyAchievements, checkMyAchievements } from '../controllers/achievementController.js';

const router = Router();

router.get('/', getMyAchievements);
router.post('/check', checkMyAchievements);

export default router;
