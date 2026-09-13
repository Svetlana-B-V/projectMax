import { Op } from 'sequelize';
import { Expense, ExpenseSplit, GroupMember, User, Category, Debt, DebtPayment } from '../models/index.js';
import { recognizeReceipt } from '../services/aiService.js';
import multer from 'multer';
import { sequelize } from '../config/db.js';

const upload = multer({ storage: multer.memoryStorage() });

// Функция пересчёта долгов в группе
async function recalculateDebts(groupId, transaction) {
  // Получаем все расходы группы с долями
  const expenses = await Expense.findAll({
    where: { groupId },
    include: [{ model: ExpenseSplit, as: 'ExpenseSplits' }],
    transaction,
  });

  // Балансы: userId -> { paid, owed }
  const balances = {};
  for (const expense of expenses) {
    const payerId = expense.payerId;
    const amount = parseFloat(expense.amount);

    if (!balances[payerId]) balances[payerId] = { paid: 0, owed: 0 };
    balances[payerId].paid += amount;

    const splits = expense.ExpenseSplits || [];
    for (const split of splits) {
      if (!balances[split.userId]) balances[split.userId] = { paid: 0, owed: 0 };
      balances[split.userId].owed += parseFloat(split.amountOwed);
    }
  }

  // Удаляем все долги группы (каскадно удалятся и DebtPayment)
  await Debt.destroy({
    where: { groupId },
    transaction,
  });

  // Вычисляем чистые балансы
  const creditors = []; // те, кому должны (paid > owed)
  const debtors = [];   // те, кто должен (owed > paid)
  for (const [userId, bal] of Object.entries(balances)) {
    const net = bal.paid - bal.owed;
    if (net > 0.01) creditors.push({ userId, net });
    else if (net < -0.01) debtors.push({ userId, net: -net });
  }

  // Жадный алгоритм создания долгов
  let i = 0, j = 0;
  while (i < debtors.length && j < creditors.length) {
    const debtor = debtors[i];
    const creditor = creditors[j];
    const amount = Math.min(debtor.net, creditor.net);

    await Debt.create({
      groupId,
      fromUserId: debtor.userId,
      toUserId: creditor.userId,
      amount,
      status: 'pending',
    }, { transaction });

    debtor.net -= amount;
    creditor.net -= amount;
    if (debtor.net < 0.01) i++;
    if (creditor.net < 0.01) j++;
  }
}

export const createExpense = async (req, res, next) => {
  const transaction = await sequelize.transaction();
  try {
    const { groupId, payerId, categoryId, amount, description, date, splits } = req.body;
    const membership = await GroupMember.findOne({ where: { groupId, userId: req.userId } });
    if (!membership) {
      await transaction.rollback();
      return res.status(403).json({ message: 'Вы не состоите в этой группе' });
    }

    let finalSplits = splits;
    if (!finalSplits) {
      const members = await GroupMember.findAll({ where: { groupId }, attributes: ['userId'] });
      const memberIds = members.map(m => m.userId);
      const share = amount / memberIds.length;
      finalSplits = memberIds.map(userId => ({ userId, amountOwed: share }));
    }

    const expense = await Expense.create({
      groupId,
      payerId,
      categoryId,
      amount,
      description,
      date: date ? new Date(date) : new Date(),
      createdById: req.userId,
    }, { transaction });

    await ExpenseSplit.bulkCreate(finalSplits.map(s => ({
      expenseId: expense.id,
      userId: s.userId,
      amountOwed: s.amountOwed,
      isPaid: s.userId === payerId,
    })), { transaction });

    // Пересчитываем долги
    await recalculateDebts(groupId, transaction);

    await transaction.commit();
    res.status(201).json(expense);
  } catch (err) {
    await transaction.rollback();
    next(err);
  }
};

export const getExpenses = async (req, res, next) => {
  try {
    const { groupId } = req.params;
    const { from, to, categoryId, userId } = req.query;
    const where = { groupId };
    if (from || to) {
      where.date = {};
      if (from) where.date[Op.gte] = new Date(from);
      if (to) where.date[Op.lte] = new Date(to);
    }
    if (categoryId) where.categoryId = categoryId;
    if (userId) {
      const splits = await ExpenseSplit.findAll({ where: { userId }, attributes: ['expenseId'] });
      const expenseIds = splits.map(s => s.expenseId);
      where[Op.or] = [
        { payerId: userId },
        { id: { [Op.in]: expenseIds } },
      ];
    }

    const expenses = await Expense.findAll({
      where,
      include: [
        { model: User, as: 'payer', attributes: ['id', 'name'] },
        { model: Category, attributes: ['id', 'name', 'icon', 'color'] },
        { model: ExpenseSplit, as: 'ExpenseSplits', include: [{ model: User, attributes: ['id', 'name'] }] },
      ],
      order: [['date', 'DESC']],
    });
    res.json(expenses);
  } catch (err) { next(err); }
};

export const updateExpense = async (req, res, next) => {
  const transaction = await sequelize.transaction();
  try {
    const expense = await Expense.findByPk(req.params.expenseId, { transaction });
    if (!expense) {
      await transaction.rollback();
      return res.status(404).json({ message: 'Расход не найден' });
    }
    if (expense.createdById !== req.userId) {
      await transaction.rollback();
      return res.status(403).json({ message: 'Только автор может изменять расход' });
    }

    await expense.update(req.body, { transaction });

    // Если изменились сумма или splits, пересчитываем долги.
    // Для простоты всегда пересчитываем долги группы при обновлении.
    const groupId = expense.groupId;
    await recalculateDebts(groupId, transaction);

    await transaction.commit();
    res.json(expense);
  } catch (err) {
    await transaction.rollback();
    next(err);
  }
};

export const deleteExpense = async (req, res, next) => {
  const transaction = await sequelize.transaction();
  try {
    const expense = await Expense.findByPk(req.params.expenseId, { transaction });
    if (!expense) {
      await transaction.rollback();
      return res.status(404).json({ message: 'Расход не найден' });
    }
    if (expense.createdById !== req.userId) {
      await transaction.rollback();
      return res.status(403).json({ message: 'Только автор может удалять расход' });
    }

    const groupId = expense.groupId;
    await expense.destroy({ transaction });
    await recalculateDebts(groupId, transaction);

    await transaction.commit();
    res.json({ message: 'Расход удалён' });
  } catch (err) {
    await transaction.rollback();
    next(err);
  }
};

export const uploadMiddleware = upload.single('photo');

export const uploadReceipt = async (req, res, next) => {
  try {
    if (!req.file) return res.status(400).json({ message: 'Файл не загружен' });
    const imageBuffer = req.file.buffer;
    const recognized = await recognizeReceipt(imageBuffer);
    res.json(recognized);
  } catch (err) { next(err); }
};