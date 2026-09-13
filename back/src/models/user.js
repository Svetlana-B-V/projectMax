import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';

const User = sequelize.define('User', {
  id: {
    type: DataTypes.UUID,
    defaultValue: DataTypes.UUIDV4,
    primaryKey: true,
  },
  telegramId: {
    type: DataTypes.BIGINT,
    unique: true,
    allowNull: true,
    field: 'telegramId',
  },
  email: {
    type: DataTypes.STRING(255),
    unique: true,
    allowNull: true,
    field: 'email',
  },
  name: {
    type: DataTypes.STRING(100),
    allowNull: false,
    field: 'name',
  },
  avatarUrl: {
    type: DataTypes.TEXT,
    allowNull: true,
    field: 'avatarUrl',
  },
}, {
  tableName: 'users',
});

export default User;