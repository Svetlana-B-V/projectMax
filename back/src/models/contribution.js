import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';
import SavingsGoal from './savingsGoal.js';
import User from './user.js';

const Contribution = sequelize.define('Contribution', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  savingsGoalId: { type: DataTypes.UUID, references: { model: SavingsGoal, key: 'id' }, field: 'savingsGoalId' },
  userId: { type: DataTypes.UUID, references: { model: User, key: 'id' }, field: 'userId' },
  amount: { type: DataTypes.DECIMAL(10, 2), allowNull: false },
  note: { type: DataTypes.TEXT },
  createDate: { type: DataTypes.DATE, defaultValue: DataTypes.NOW, field: 'createDate' },
}, {
  tableName: 'contributions',
  timestamps: false,
});

export default Contribution;