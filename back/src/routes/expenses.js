import { Router } from 'express';
import { createExpense, getExpenses, updateExpense, deleteExpense, uploadReceipt, uploadMiddleware } from '../controllers/expenseController.js';
import { validate } from '../middlewares/validate.js';
import { createExpenseSchema, updateExpenseSchema } from '../schemas/expenseSchema.js';

const router = Router();

router.post('/', validate(createExpenseSchema), createExpense);
router.get('/group/:groupId', getExpenses);
router.put('/:expenseId', validate(updateExpenseSchema), updateExpense);
router.delete('/:expenseId', deleteExpense);
router.post('/receipt', uploadMiddleware, uploadReceipt);

export default router;