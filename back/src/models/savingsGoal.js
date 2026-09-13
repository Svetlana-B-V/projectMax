import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';
import Group from './group.js';
import User from './user.js';

const SavingsGoal = sequelize.define('SavingsGoal', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  groupId: { type: DataTypes.UUID, references: { model: Group, key: 'id' }, field: 'groupId' },
  name: { type: DataTypes.STRING(100), allowNull: false },
  type: { type: DataTypes.STRING(20), allowNull: false, defaultValue: 'group' },
  targetAmount: { type: DataTypes.DECIMAL(10, 2), allowNull: false, field: 'targetAmount' },
  currentAmount: { type: DataTypes.DECIMAL(10, 2), allowNull: false, defaultValue: 0, field: 'currentAmount' },
  createdBy: { type: DataTypes.UUID, references: { model: User, key: 'id' }, field: 'createdBy' },
  deadline: { type: DataTypes.DATE },
  status: { type: DataTypes.STRING(20), allowNull: false, defaultValue: 'active' },
}, {
  tableName: 'savings_goals',
});

export default SavingsGoal;