import { listAchievements, checkAchievements } from '../services/achievementService.js';

export const getMyAchievements = async (req, res, next) => {
  try {
    res.json(await listAchievements(req.userId));
  } catch (err) { next(err); }
};

export const checkMyAchievements = async (req, res, next) => {
  try {
    res.json(await checkAchievements(req.userId));
  } catch (err) { next(err); }
};
