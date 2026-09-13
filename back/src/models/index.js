import { sequelize } from '../config/db.js';
import User from './user.js';
import Session from './session.js';
import Group from './group.js';
import GroupMember from './groupMember.js';
import Category from './category.js';
import Expense from './expense.js';
import ExpenseSplit from './expenseSplit.js';
import Debt from './debt.js';
import DebtPayment from './debtPayment.js';
import SavingsGoal from './savingsGoal.js';
import Contribution from './contribution.js';
import ReminderSettings from './reminderSettings.js';
import Achievement from './achievement.js';
import UserAchievement from './userAchievement.js';

// Связи
User.hasMany(Session, { foreignKey: 'userId' });
Session.belongsTo(User, { foreignKey: 'userId' });

User.hasMany(GroupMember, { foreignKey: 'userId' });
GroupMember.belongsTo(User, { foreignKey: 'userId' });

Group.hasMany(GroupMember, { foreignKey: 'groupId' });
GroupMember.belongsTo(Group, { foreignKey: 'groupId' });

Group.belongsTo(User, { as: 'owner', foreignKey: 'ownerId' });

Group.hasMany(Expense, { foreignKey: 'groupId' });
Expense.belongsTo(Group, { foreignKey: 'groupId' });

User.hasMany(Expense, { as: 'paidExpenses', foreignKey: 'payerId' });
Expense.belongsTo(User, { as: 'payer', foreignKey: 'payerId' });

User.hasMany(Expense, { as: 'createdExpenses', foreignKey: 'createdById' });
Expense.belongsTo(User, { as: 'creator', foreignKey: 'createdById' });

Category.hasMany(Expense, { foreignKey: 'categoryId' });
Expense.belongsTo(Category, { foreignKey: 'categoryId' });

Expense.hasMany(ExpenseSplit, { foreignKey: 'expenseId', as: 'ExpenseSplits' });
ExpenseSplit.belongsTo(Expense, { foreignKey: 'expenseId' });

User.hasMany(ExpenseSplit, { foreignKey: 'userId' });
ExpenseSplit.belongsTo(User, { foreignKey: 'userId' });

Group.hasMany(Debt, { foreignKey: 'groupId' });
Debt.belongsTo(Group, { foreignKey: 'groupId' });

User.hasMany(Debt, { as: 'debtsFrom', foreignKey: 'fromUserId' });
User.hasMany(Debt, { as: 'debtsTo', foreignKey: 'toUserId' });
Debt.belongsTo(User, { as: 'fromUser', foreignKey: 'fromUserId' });
Debt.belongsTo(User, { as: 'toUser', foreignKey: 'toUserId' });

Debt.hasMany(DebtPayment, { foreignKey: 'debtId' });
DebtPayment.belongsTo(Debt, { foreignKey: 'debtId' });

Group.hasMany(SavingsGoal, { foreignKey: 'groupId' });
SavingsGoal.belongsTo(Group, { foreignKey: 'groupId' });

User.hasMany(SavingsGoal, { as: 'createdGoals', foreignKey: 'createdBy' });
SavingsGoal.belongsTo(User, { as: 'creator', foreignKey: 'createdBy' });

SavingsGoal.hasMany(Contribution, { foreignKey: 'savingsGoalId' });
Contribution.belongsTo(SavingsGoal, { foreignKey: 'savingsGoalId' });

User.hasMany(Contribution, { foreignKey: 'userId' });
Contribution.belongsTo(User, { foreignKey: 'userId' });

User.hasOne(ReminderSettings, { foreignKey: 'userId' });
ReminderSettings.belongsTo(User, { foreignKey: 'userId' });

User.hasMany(UserAchievement, { foreignKey: 'userId' });
UserAchievement.belongsTo(User, { foreignKey: 'userId' });
Achievement.hasMany(UserAchievement, { foreignKey: 'achievementCode' });
UserAchievement.belongsTo(Achievement, { foreignKey: 'achievementCode' });

export {
  sequelize,
  User,
  Session,
  Group,
  GroupMember,
  Category,
  Expense,
  ExpenseSplit,
  Debt,
  DebtPayment,
  SavingsGoal,
  Contribution,
  ReminderSettings,
  Achievement,
  UserAchievement,
};