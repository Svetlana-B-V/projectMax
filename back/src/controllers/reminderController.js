import { ReminderSettings } from '../models/index.js';

async function getOrCreate(userId) {
  const [settings] = await ReminderSettings.findOrCreate({
    where: { userId },
    defaults: { userId, style: 'neutral', enabled: true },
  });
  return settings;
}

export const getMyReminders = async (req, res, next) => {
  try {
    const settings = await getOrCreate(req.userId);
    res.json(settings);
  } catch (err) { next(err); }
};

export const updateMyReminders = async (req, res, next) => {
  try {
    const settings = await getOrCreate(req.userId);
    await settings.update(req.body);
    res.json(settings);
  } catch (err) { next(err); }
};

export const ackReminder = async (req, res, next) => {
  try {
    const settings = await getOrCreate(req.userId);
    settings.lastRemindedAt = new Date();
    await settings.save();
    res.json(settings);
  } catch (err) { next(err); }
};
