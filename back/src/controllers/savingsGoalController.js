import { SavingsGoal, Contribution, User } from '../models/index.js';
import { sequelize } from '../config/db.js';

export const createSavingsGoal = async (req, res, next) => {
  try {
    const { groupId, name, type, targetAmount, deadline } = req.body;
    const goal = await SavingsGoal.create({
      groupId,
      name,
      type,
      targetAmount,
      deadline: deadline ? new Date(deadline) : null,
      createdBy: req.userId,
    });
    res.status(201).json(goal);
  } catch (err) { next(err); }
};

export const getSavingsGoals = async (req, res, next) => {
  try {
    const { groupId } = req.params;
    const goals = await SavingsGoal.findAll({
      where: { groupId },
      include: [{ model: Contribution, include: [{ model: User, attributes: ['id', 'name'] }] }],
      order: [['createDate', 'DESC']],
    });
    res.json(goals);
  } catch (err) { next(err); }
};

export const contribute = async (req, res, next) => {
  const transaction = await sequelize.transaction();
  try {
    const { goalId } = req.params;
    const { amount, note } = req.body;
    const goal = await SavingsGoal.findByPk(goalId, { transaction });
    if (!goal) {
      await transaction.rollback();
      return res.status(404).json({ message: 'Копилка не найдена' });
    }

    await Contribution.create({ savingsGoalId: goalId, userId: req.userId, amount, note }, { transaction });
    goal.currentAmount = parseFloat(goal.currentAmount) + amount;
    if (goal.currentAmount >= goal.targetAmount && goal.status !== 'completed') {
      goal.status = 'completed';
    }
    await goal.save({ transaction });
    await transaction.commit();
    res.json(goal);
  } catch (err) {
    await transaction.rollback();
    next(err);
  }
};