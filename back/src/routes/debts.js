import { Router } from 'express';
import { getGroupDebts, getMyDebts, payDebt } from '../controllers/debtController.js';
import { validate } from '../middlewares/validate.js';
import { payDebtSchema } from '../schemas/debtSchema.js';

const router = Router();

router.get('/group/:groupId', getGroupDebts);
router.get('/my', getMyDebts);
router.post('/:debtId/pay', validate(payDebtSchema), payDebt);

export default router;