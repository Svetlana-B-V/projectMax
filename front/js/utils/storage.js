import CONFIG from '../config.js';

export const storage = {
    getToken() {
        return localStorage.getItem(CONFIG.TOKEN_KEY);
    },

    setToken(token) {
        if (token) {
            localStorage.setItem(CONFIG.TOKEN_KEY, token);
        } else {
            localStorage.removeItem(CONFIG.TOKEN_KEY);
        }
    },

    getUser() {
        const user = localStorage.getItem(CONFIG.USER_KEY);
        return user ? JSON.parse(user) : null;
    },

    setUser(user) {
        if (user) {
            localStorage.setItem(CONFIG.USER_KEY, JSON.stringify(user));
        } else {
            localStorage.removeItem(CONFIG.USER_KEY);
        }
    },

    getActiveGroup() {
        const group = localStorage.getItem(CONFIG.GROUP_KEY);
        return group ? JSON.parse(group) : null;
    },

    setActiveGroup(group) {
        if (group) {
            localStorage.setItem(CONFIG.GROUP_KEY, JSON.stringify(group));
        } else {
            localStorage.removeItem(CONFIG.GROUP_KEY);
        }
    },

    clear() {
        localStorage.removeItem(CONFIG.TOKEN_KEY);
        localStorage.removeItem(CONFIG.USER_KEY);
        localStorage.removeItem(CONFIG.GROUP_KEY);
    },
};