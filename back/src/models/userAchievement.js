import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';
import User from './user.js';
import Achievement from './achievement.js';

const UserAchievement = sequelize.define('UserAchievement', {
  userId: {
    type: DataTypes.UUID,
    primaryKey: true,
    references: { model: User, key: 'id' },
    field: 'userId',
  },
  achievementCode: {
    type: DataTypes.STRING(50),
    primaryKey: true,
    references: { model: Achievement, key: 'code' },
    field: 'achievementCode',
  },
  earnedAt: {
    type: DataTypes.DATE,
    allowNull: false,
    defaultValue: DataTypes.NOW,
    field: 'earnedAt',
  },
}, {
  tableName: 'user_achievements',
  timestamps: false,
});

export default UserAchievement;
