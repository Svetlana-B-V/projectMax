import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';
import Group from './group.js';
import User from './user.js';

const GroupMember = sequelize.define('GroupMember', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  groupId: { type: DataTypes.UUID, references: { model: Group, key: 'id' }, field: 'groupId' },
  userId: { type: DataTypes.UUID, references: { model: User, key: 'id' }, field: 'userId' },
  role: { type: DataTypes.STRING(20), allowNull: false, defaultValue: 'member' },
  joinedAt: { type: DataTypes.DATE, allowNull: false, defaultValue: DataTypes.NOW, field: 'joinedAt' },
}, {
  tableName: 'group_members',
  timestamps: false,
});

export default GroupMember;