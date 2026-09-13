import { Op } from 'sequelize';
import { Expense, Category, User, Group, GroupMember, ExpenseSplit, Debt } from '../models/index.js';
import { startOfMonth, endOfMonth, format } from 'date-fns';

// Групповая сводка за месяц
export const getMonthlySummary = async (req, res, next) => {
  try {
    const { groupId } = req.params;
    const month = req.query.month || format(new Date(), 'yyyy-MM');
    const start = startOfMonth(new Date(month));
    const end = endOfMonth(new Date(month));

    const expenses = await Expense.findAll({
      where: { groupId, date: { [Op.between]: [start, end] } },
      include: [
        { model: Category, attributes: ['name'] },
        { model: User, as: 'payer', attributes: ['name'] },
      ],
    });

    const total = expenses.reduce((sum, e) => sum + parseFloat(e.amount), 0);
    const byCategory = {};
    const byPayer = {};
    expenses.forEach(e => {
      const catName = e.Category?.name || 'Без категории';
      byCategory[catName] = (byCategory[catName] || 0) + parseFloat(e.amount);
      const payerName = e.payer?.name || 'Неизвестно';
      byPayer[payerName] = (byPayer[payerName] || 0) + parseFloat(e.amount);
    });
    res.json({ total, byCategory, byPayer });
  } catch (err) { next(err); }
};

// Групповая аналитика по дням
export const getDailyAnalytics = async (req, res, next) => {
  try {
    const { groupId } = req.params;
    const { from, to } = req.query;
    const where = { groupId };
    if (from) where.date = { ...where.date, [Op.gte]: new Date(from) };
    if (to) where.date = { ...where.date, [Op.lte]: new Date(to) };

    const expenses = await Expense.findAll({
      where,
      attributes: ['date', 'amount'],
      order: [['date', 'ASC']],
    });

    const daily = {};
    expenses.forEach(e => {
      const day = format(e.date, 'yyyy-MM-dd');
      daily[day] = (daily[day] || 0) + parseFloat(e.amount);
    });
    res.json(daily);
  } catch (err) { next(err); }
};

// Прогноз бюджета группы
export const getBudgetPrediction = async (req, res, next) => {
  try {
    const { groupId } = req.params;
    const start = startOfMonth(new Date());
    const expenses = await Expense.findAll({
      where: { groupId, date: { [Op.gte]: start } },
      attributes: ['amount'],
    });
    const totalSpent = expenses.reduce((s, e) => s + parseFloat(e.amount), 0);
    const daysPassed = new Date().getDate();
    const daysInMonth = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).getDate();
    const projectedTotal = Math.round((totalSpent / daysPassed) * daysInMonth);
    const dailyAvg = Math.round(totalSpent / daysPassed);
    res.json({ totalSpent: Math.round(totalSpent), projectedTotal, dailyAvg });
  } catch (err) { next(err); }
};

// Персональная сводка за месяц + текущие долги
export const getMyMonthlySummary = async (req, res, next) => {
  try {
    const userId = req.userId;
    const month = req.query.month || format(new Date(), 'yyyy-MM');
    const start = startOfMonth(new Date(month));
    const end = endOfMonth(new Date(month));

    // Все группы пользователя
    const memberships = await GroupMember.findAll({ where: { userId }, attributes: ['groupId'] });
    const groupIds = memberships.map(m => m.groupId);
    if (groupIds.length === 0) {
      return res.json({
        totalSpent: 0,
        byCategory: {},
        byGroup: {},
        debtsOwed: [],
        debtsOwedToMe: [],
      });
    }

    // Расходы из этих групп за период
    const expenses = await Expense.findAll({
      where: {
        groupId: { [Op.in]: groupIds },
        date: { [Op.between]: [start, end] },
      },
      include: [
        { model: Category, attributes: ['id', 'name'] },
        { model: Group, attributes: ['id', 'name'] },
        { model: ExpenseSplit, as: 'ExpenseSplits', attributes: ['userId', 'amountOwed'] },
      ],
    });

    let totalSpent = 0;
    const byCategory = {};
    const byGroup = {};

    for (const expense of expenses) {
      const split = (expense.ExpenseSplits || []).find(s => s.userId === userId);
      let userShare;
      if (split) {
        userShare = parseFloat(split.amountOwed);
      } else if (expense.payerId === userId) {
        userShare = parseFloat(expense.amount);
      } else {
        continue;
      }

      totalSpent += userShare;

      const catName = expense.Category?.name || 'Без категории';
      byCategory[catName] = (byCategory[catName] || 0) + userShare;

      const groupName = expense.Group?.name || expense.groupId;
      byGroup[groupName] = (byGroup[groupName] || 0) + userShare;
    }

    // Текущие долги пользователя (status = 'pending')
    const debtsOwed = await Debt.findAll({
      where: { fromUserId: userId, status: 'pending' },
      include: [{ model: User, as: 'toUser', attributes: ['id', 'name'] }],
    });

    const debtsOwedToMe = await Debt.findAll({
      where: { toUserId: userId, status: 'pending' },
      include: [{ model: User, as: 'fromUser', attributes: ['id', 'name'] }],
    });

    res.json({
      totalSpent,
      byCategory,
      byGroup,
      debtsOwed: debtsOwed.map(d => ({
        toUser: d.toUser?.name || 'Неизвестно',
        amount: parseFloat(d.amount),
      })),
      debtsOwedToMe: debtsOwedToMe.map(d => ({
        fromUser: d.fromUser?.name || 'Неизвестно',
        amount: parseFloat(d.amount),
      })),
    });
  } catch (err) { next(err); }
};