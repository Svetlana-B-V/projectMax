import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';
import Expense from './expense.js';
import User from './user.js';

const ExpenseSplit = sequelize.define('ExpenseSplit', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  expenseId: { type: DataTypes.UUID, references: { model: Expense, key: 'id' }, field: 'expenseId' },
  userId: { type: DataTypes.UUID, references: { model: User, key: 'id' }, field: 'userId' },
  amountOwed: { type: DataTypes.DECIMAL(10, 2), allowNull: false, field: 'amountOwed' },
  isPaid: { type: DataTypes.BOOLEAN, allowNull: false, defaultValue: false, field: 'isPaid' },
}, {
  tableName: 'expense_splits',
  timestamps: false,
});

export default ExpenseSplit;