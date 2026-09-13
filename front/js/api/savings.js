import { api } from './api.js';

export const savingsApi = {
    async getByGroup(groupId) {
        return api.get(`/savings-goals/group/${groupId}`);
    },

    async create(data) {
        return api.post('/savings-goals', data);
    },

    async contribute(goalId, amount, note = null) {
        return api.post(`/savings-goals/${goalId}/contribute`, { amount, note });
    },
};