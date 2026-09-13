import { api } from './api.js';

export const groupsApi = {
    async getMyGroups() {
        return api.get('/groups/my');
    },

    async createGroup(name, currency = 'RUB') {
        return api.post('/groups', { name, currency });
    },

    async joinGroup(inviteCode) {
        return api.post('/groups/join', { inviteCode });
    },

    async getMembers(groupId) {
        return api.get(`/groups/${groupId}/members`);
    },
};