import { api } from './api.js';

export const analyticsApi = {
    async getGroupSummary(groupId, month = null) {
        const query = month ? `?month=${month}` : '';
        return api.get(`/analytics/group/${groupId}/summary${query}`);
    },

    async getMySummary(month = null) {
        const query = month ? `?month=${month}` : '';
        return api.get(`/analytics/my/summary${query}`);
    },

    async getDaily(groupId, from = null, to = null) {
        const params = new URLSearchParams();
        if (from) params.append('from', from);
        if (to) params.append('to', to);
        return api.get(`/analytics/group/${groupId}/daily?${params.toString()}`);
    },

    async getPrediction(groupId) {
        return api.get(`/analytics/group/${groupId}/prediction`);
    },
};