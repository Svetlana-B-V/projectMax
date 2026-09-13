import { api } from './api.js';

export const expensesApi = {
    async getByGroup(groupId, filters = {}) {
        const params = new URLSearchParams();
        if (filters.from) params.append('from', filters.from);
        if (filters.to) params.append('to', filters.to);
        if (filters.categoryId) params.append('categoryId', filters.categoryId);
        if (filters.userId) params.append('userId', filters.userId);

        const query = params.toString();
        return api.get(`/expenses/group/${groupId}${query ? `?${query}` : ''}`);
    },

    async create(data) {
        return api.post('/expenses', data);
    },

    async update(id, data) {
        return api.put(`/expenses/${id}`, data);
    },

    async delete(id) {
        return api.delete(`/expenses/${id}`);
    },

    async uploadReceipt(file) {
        const formData = new FormData();
        formData.append('photo', file);
        return api.post('/expenses/receipt', formData, true);
    },
};