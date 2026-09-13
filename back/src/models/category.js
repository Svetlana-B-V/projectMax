import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';
import Group from './group.js';

const Category = sequelize.define('Category', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  name: { type: DataTypes.STRING(100), allowNull: false },
  icon: { type: DataTypes.STRING(50) },
  color: { type: DataTypes.STRING(20) },
  isDefault: { type: DataTypes.BOOLEAN, allowNull: false, defaultValue: false, field: 'isDefault' },
  groupId: { type: DataTypes.UUID, references: { model: Group, key: 'id' }, field: 'groupId' },
}, {
  tableName: 'categories',
  timestamps: false,
});

export default Category;