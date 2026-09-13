import { api } from './api.js';

export const debtsApi = {
    async getByGroup(groupId) {
        return api.get(`/debts/group/${groupId}`);
    },

    async getMy() {
        return api.get('/debts/my');
    },

    async pay(debtId, amount) {
        return api.post(`/debts/${debtId}/pay`, { amount });
    },
};