import { api } from './api.js';

export const categoriesApi = {
    async getAll(groupId = null) {
        const query = groupId ? `?groupId=${groupId}` : '';
        return api.get(`/categories${query}`);
    },

    async create(data) {
        return api.post('/categories', data);
    },

    async update(id, data) {
        return api.put(`/categories/${id}`, data);
    },

    async delete(id) {
        return api.delete(`/categories/${id}`);
    },
};