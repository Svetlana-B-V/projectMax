import { Op } from 'sequelize';
import { Debt, DebtPayment, User } from '../models/index.js';
import { sequelize } from '../config/db.js';

export const getGroupDebts = async (req, res, next) => {
  try {
    const { groupId } = req.params;
    const debts = await Debt.findAll({
      where: { groupId, status: 'pending' },
      include: [
        { model: User, as: 'fromUser', attributes: ['id', 'name', 'telegramId'] },
        { model: User, as: 'toUser', attributes: ['id', 'name', 'telegramId'] },
      ],
    });
    res.json(debts);
  } catch (err) { next(err); }
};

export const getMyDebts = async (req, res, next) => {
  try {
    const userId = req.userId;
    const debts = await Debt.findAll({
      where: {
        status: 'pending',
        [Op.or]: [{ fromUserId: userId }, { toUserId: userId }],
      },
      include: [
        { model: User, as: 'fromUser', attributes: ['id', 'name'] },
        { model: User, as: 'toUser', attributes: ['id', 'name'] },
      ],
    });
    res.json(debts);
  } catch (err) { next(err); }
};

export const payDebt = async (req, res, next) => {
  const transaction = await sequelize.transaction();
  try {
    const { debtId } = req.params;
    const { amount } = req.body;
    const debt = await Debt.findByPk(debtId, { transaction });
    if (!debt || debt.status !== 'pending') {
      await transaction.rollback();
      return res.status(404).json({ message: 'Долг не найден или уже погашен' });
    }
    if (amount > parseFloat(debt.amount)) {
      await transaction.rollback();
      return res.status(400).json({ message: 'Сумма превышает остаток долга' });
    }
    await DebtPayment.create({ debtId, amount }, { transaction });
    const newAmount = parseFloat(debt.amount) - amount;
    if (newAmount === 0) {
      debt.status = 'settled';
    }
    debt.amount = newAmount;
    await debt.save({ transaction });
    await transaction.commit();
    res.json(debt);
  } catch (err) {
    await transaction.rollback();
    next(err);
  }
};