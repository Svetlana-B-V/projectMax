import { Router } from 'express';
import { loginByTelegram, linkEmail, logout } from '../controllers/authController.js';
import { validate } from '../middlewares/validate.js';
import { loginByTelegramSchema, linkEmailSchema } from '../schemas/authSchema.js';
import { auth } from '../middlewares/auth.js';

const router = Router();

router.post('/telegram', validate(loginByTelegramSchema), loginByTelegram);
router.post('/link-email', auth, validate(linkEmailSchema), linkEmail);
router.post('/logout', auth, logout);

export default router;