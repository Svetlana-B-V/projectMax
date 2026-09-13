import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';
import User from './user.js';

const Group = sequelize.define('Group', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  name: { type: DataTypes.STRING(100), allowNull: false },
  currency: { type: DataTypes.STRING(10), allowNull: false, defaultValue: 'RUB' },
  inviteCode: { type: DataTypes.STRING(10), unique: true, allowNull: false, field: 'inviteCode' },
  ownerId: { type: DataTypes.UUID, references: { model: User, key: 'id' }, field: 'ownerId' },
}, { tableName: 'groups' });

export default Group;