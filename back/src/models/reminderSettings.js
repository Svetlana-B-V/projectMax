import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';
import User from './user.js';

const ReminderSettings = sequelize.define('ReminderSettings', {
  userId: {
    type: DataTypes.UUID,
    primaryKey: true,
    references: { model: User, key: 'id' },
    field: 'userId',
  },
  style: {
    type: DataTypes.STRING(20),
    allowNull: false,
    defaultValue: 'neutral',
  },
  enabled: {
    type: DataTypes.BOOLEAN,
    allowNull: false,
    defaultValue: true,
  },
  lastRemindedAt: {
    type: DataTypes.DATE,
    allowNull: true,
    field: 'lastRemindedAt',
  },
}, {
  tableName: 'reminder_settings',
  timestamps: false,
});

export default ReminderSettings;
