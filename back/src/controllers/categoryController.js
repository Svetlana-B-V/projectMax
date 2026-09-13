import { Op } from 'sequelize';
import { Category } from '../models/index.js';

export const getCategories = async (req, res, next) => {
  try {
    const { groupId } = req.query;
    const where = groupId ? { [Op.or]: [{ groupId }, { groupId: null }] } : { groupId: null };
    const categories = await Category.findAll({ where });
    res.json(categories);
  } catch (err) { next(err); }
};

export const createCategory = async (req, res, next) => {
  try {
    const { name, icon, color, groupId } = req.body;
    const category = await Category.create({ name, icon, color, groupId });
    res.status(201).json(category);
  } catch (err) { next(err); }
};

export const updateCategory = async (req, res, next) => {
  try {
    const category = await Category.findByPk(req.params.categoryId);
    if (!category) return res.status(404).json({ message: 'Категория не найдена' });
    await category.update(req.body);
    res.json(category);
  } catch (err) { next(err); }
};

export const deleteCategory = async (req, res, next) => {
  try {
    const category = await Category.findByPk(req.params.categoryId);
    if (!category) return res.status(404).json({ message: 'Категория не найдена' });
    await category.destroy();
    res.json({ message: 'Категория удалена' });
  } catch (err) { next(err); }
};