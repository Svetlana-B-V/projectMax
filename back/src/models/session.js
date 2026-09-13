import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';
import User from './user.js';

const Session = sequelize.define('Session', {
  id: {
    type: DataTypes.UUID,
    defaultValue: DataTypes.UUIDV4,
    primaryKey: true,
  },
  userId: {
    type: DataTypes.UUID,
    references: { model: User, key: 'id' },
    field: 'userId',
  },
  token: {
    type: DataTypes.TEXT,
    allowNull: false,
    unique: true,
  },
  expiresAt: {
    type: DataTypes.DATE,
    allowNull: true,
    field: 'expiresAt',
  },
  createDate: {
    type: DataTypes.DATE,
    defaultValue: DataTypes.NOW,
    field: 'createDate',
  },
}, {
  tableName: 'sessions',
  timestamps: false,
});

export default Session;