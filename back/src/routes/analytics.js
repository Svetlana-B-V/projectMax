import { Router } from 'express';
import {
  getMonthlySummary,
  getDailyAnalytics,
  getBudgetPrediction,
  getMyMonthlySummary, // ← эта функция должна быть импортирована
} from '../controllers/analyticsController.js';

const router = Router();

router.get('/group/:groupId/summary', getMonthlySummary);
router.get('/group/:groupId/daily', getDailyAnalytics);
router.get('/group/:groupId/prediction', getBudgetPrediction);

// Новый маршрут для персональной сводки
router.get('/my/summary', getMyMonthlySummary); // ← эта строка обязательна

export default router;