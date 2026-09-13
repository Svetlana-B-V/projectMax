import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';

const Achievement = sequelize.define('Achievement', {
  code: { type: DataTypes.STRING(50), primaryKey: true },
  name: { type: DataTypes.STRING(100), allowNull: false },
  description: { type: DataTypes.TEXT, allowNull: false },
  icon: { type: DataTypes.STRING(20) },
}, {
  tableName: 'achievements',
  timestamps: false,
});

export default Achievement;
