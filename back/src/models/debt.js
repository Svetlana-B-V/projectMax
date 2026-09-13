import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';
import Group from './group.js';
import User from './user.js';

const Debt = sequelize.define('Debt', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  groupId: { type: DataTypes.UUID, references: { model: Group, key: 'id' }, field: 'groupId' },
  fromUserId: { type: DataTypes.UUID, references: { model: User, key: 'id' }, field: 'fromUserId' },
  toUserId: { type: DataTypes.UUID, references: { model: User, key: 'id' }, field: 'toUserId' },
  amount: { type: DataTypes.DECIMAL(10, 2), allowNull: false },
  status: { type: DataTypes.STRING(20), allowNull: false, defaultValue: 'pending' },
}, {
  tableName: 'debts',
});

export default Debt;