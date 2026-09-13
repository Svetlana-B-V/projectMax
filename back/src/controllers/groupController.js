import { Group, GroupMember, User } from '../models/index.js';
import { generateInviteCode } from '../utils/generateInviteCode.js';

export const createGroup = async (req, res, next) => {
  try {
    const { name, currency } = req.body;
    const inviteCode = generateInviteCode();
    const group = await Group.create({ name, currency, inviteCode, ownerId: req.userId });
    await GroupMember.create({ groupId: group.id, userId: req.userId, role: 'owner' });
    res.status(201).json(group);
  } catch (err) { next(err); }
};

export const getMyGroups = async (req, res, next) => {
  try {
    const memberships = await GroupMember.findAll({
      where: { userId: req.userId },
      include: [{ model: Group, include: [{ model: GroupMember, include: [User] }] }],
    });
    res.json(memberships.map(m => m.Group));
  } catch (err) { next(err); }
};

export const joinGroup = async (req, res, next) => {
  try {
    const { inviteCode } = req.body;
    const group = await Group.findOne({ where: { inviteCode } });
    if (!group) return res.status(404).json({ message: 'Группа не найдена' });
    const existing = await GroupMember.findOne({ where: { groupId: group.id, userId: req.userId } });
    if (existing) return res.status(400).json({ message: 'Вы уже состоите в этой группе' });
    await GroupMember.create({ groupId: group.id, userId: req.userId, role: 'member' });
    res.json({ message: 'Вы вступили в группу', groupId: group.id });
  } catch (err) { next(err); }
};

export const getGroupMembers = async (req, res, next) => {
  try {
    const members = await GroupMember.findAll({
      where: { groupId: req.params.groupId },
      include: [{ model: User, attributes: ['id', 'name', 'avatarUrl', 'email'] }],
    });
    res.json(members);
  } catch (err) { next(err); }
};