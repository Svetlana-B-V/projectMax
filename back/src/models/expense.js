import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';
import Group from './group.js';
import User from './user.js';
import Category from './category.js';

const Expense = sequelize.define('Expense', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  groupId: { type: DataTypes.UUID, references: { model: Group, key: 'id' }, field: 'groupId' },
  payerId: { type: DataTypes.UUID, references: { model: User, key: 'id' }, field: 'payerId' },
  categoryId: { type: DataTypes.UUID, references: { model: Category, key: 'id' }, field: 'categoryId' },
  createdById: { type: DataTypes.UUID, references: { model: User, key: 'id' }, field: 'createdById', allowNull: true },
  amount: { type: DataTypes.DECIMAL(10, 2), allowNull: false },
  description: { type: DataTypes.TEXT },
  date: { type: DataTypes.DATE, allowNull: false, defaultValue: DataTypes.NOW },
  receiptPhotoUrl: { type: DataTypes.TEXT, field: 'receiptPhotoUrl' },
}, {
  tableName: 'expenses',
});

export default Expense;