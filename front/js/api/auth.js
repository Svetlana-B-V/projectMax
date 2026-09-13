import { api } from './api.js';
import { storage } from '../utils/storage.js';

export const authApi = {
    async loginByTelegram(telegramId, name) {
        const data = await api.post('/auth/telegram', { telegramId, name });
        storage.setToken(data.accessToken);
        storage.setUser(data.user);
        return data;
    },

    async logout() {
        try {
            await api.post('/auth/logout');
        } catch (err) {
            console.error('Ошибка при выходе:', err);
        } finally {
            storage.clear();
            window.location.href = '/login.html';
        }
    },

    async linkEmail(email) {
        return api.post('/auth/link-email', { email });
    },

    isAuthenticated() {
        return !!storage.getToken();
    },

    getUser() {
        return storage.getUser();
    },
};