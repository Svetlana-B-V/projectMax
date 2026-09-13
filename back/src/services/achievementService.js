import { QueryTypes } from 'sequelize';
import {
  sequelize,
  Achievement,
  UserAchievement,
  Expense,
  Contribution,
  Group,
} from '../models/index.js';

async function paymentCount(userId) {
  const rows = await sequelize.query(
    `SELECT COUNT(*)::int AS n
     FROM debt_payments p
     JOIN debts d ON d.id = p."debtId"
     WHERE d."fromUserId" = :userId`,
    { replacements: { userId }, type: QueryTypes.SELECT },
  );
  return rows[0]?.n ?? 0;
}

async function progress(userId) {
  const [expenses, contributions, groups, payments] = await Promise.all([
    Expense.count({ where: { createdById: userId } }),
    Contribution.count({ where: { userId } }),
    Group.count({ where: { ownerId: userId } }),
    paymentCount(userId),
  ]);
  return { expenses, contributions, groups, payments };
}

function earnedCodes(stats) {
  const codes = [];
  if (stats.expenses >= 1) codes.push('first_expense');
  if (stats.expenses >= 3) codes.push('three_expenses');
  if (stats.payments >= 1) codes.push('first_payment');
  if (stats.contributions >= 1) codes.push('first_contribute');
  if (stats.groups >= 1) codes.push('first_group');
  return codes;
}

export async function listAchievements(userId) {
  const catalog = await Achievement.findAll({ order: [['code', 'ASC']] });
  const mine = await UserAchievement.findAll({ where: { userId } });
  const earnedAt = Object.fromEntries(mine.map(row => [row.achievementCode, row.earnedAt]));
  return catalog.map(item => ({
    code: item.code,
    name: item.name,
    description: item.description,
    icon: item.icon,
    earnedAt: earnedAt[item.code] || null,
  }));
}

export async function checkAchievements(userId) {
  const stats = await progress(userId);
  const already = new Set(
    (await UserAchievement.findAll({ where: { userId }, attributes: ['achievementCode'] }))
      .map(row => row.achievementCode),
  );
  const fresh = earnedCodes(stats).filter(code => !already.has(code));
  if (!fresh.length) {
    return [];
  }
  await UserAchievement.bulkCreate(
    fresh.map(code => ({ userId, achievementCode: code })),
  );
  const catalog = await Achievement.findAll({ where: { code: fresh } });
  return catalog.map(item => ({
    code: item.code,
    name: item.name,
    description: item.description,
    icon: item.icon,
  }));
}
