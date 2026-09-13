import jwt from 'jsonwebtoken';
import { User, Session } from '../models/index.js';
import { env } from '../config/env.js';

const createSession = async (userId) => {
  const token = jwt.sign({ userId }, env.jwtSecret, { expiresIn: '1y' }); // длительный срок, но мы не проверяем expiration
  // Не передаём expiresAt, оставляем NULL
  await Session.create({ userId, token });
  return token;
};

// Вход/регистрация по telegramId
export const loginByTelegram = async (req, res, next) => {
  try {
    const { telegramId, name, avatarUrl } = req.body;
    let user = await User.findOne({ where: { telegramId } });
    if (!user) {
      user = await User.create({ telegramId, name: name || 'Пользователь', avatarUrl });
    }
    const accessToken = await createSession(user.id);
    res.json({ user: { id: user.id, telegramId: user.telegramId, name: user.name, email: user.email }, accessToken });
  } catch (err) { next(err); }
};

// Привязка email
export const linkEmail = async (req, res, next) => {
  try {
    const { email } = req.body;
    await User.update({ email }, { where: { id: req.userId } });
    res.json({ message: 'Email привязан', email });
  } catch (err) { next(err); }
};

// Выход (удаление сессии)
export const logout = async (req, res, next) => {
  try {
    const token = req.headers.authorization?.split(' ')[1];
    if (!token) return res.status(401).json({ message: 'Требуется авторизация' });
    await Session.destroy({ where: { token } });
    res.json({ message: 'Выход выполнен' });
  } catch (err) { next(err); }
};