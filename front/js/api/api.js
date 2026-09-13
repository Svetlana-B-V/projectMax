import CONFIG from '../config.js';
import { storage } from '../utils/storage.js';

class ApiClient {
    constructor() {
        this.baseUrl = CONFIG.API_BASE_URL;
    }

    async request(method, path, body = null, isFormData = false) {
        const url = `${this.baseUrl}${path}`;
        const headers = {};

        if (!isFormData && body) {
            headers['Content-Type'] = 'application/json';
        }

        const token = storage.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const options = { method, headers };

        if (body) {
            options.body = isFormData ? body : JSON.stringify(body);
        }

        try {
            const response = await fetch(url, options);

            // Если 204 No Content
            if (response.status === 204) {
                return null;
            }

            const data = await response.json();

            if (!response.ok) {
                const error = new Error(data.message || 'Ошибка запроса');
                error.status = response.status;
                error.data = data;
                throw error;
            }

            return data;
        } catch (err) {
            if (err.status === 401) {
                storage.clear();
                if (!window.location.pathname.includes('login.html')) {
                    window.location.href = '/login.html';
                }
            }
            throw err;
        }
    }

    get(path) {
        return this.request('GET', path);
    }

    post(path, body, isFormData = false) {
        return this.request('POST', path, body, isFormData);
    }

    put(path, body) {
        return this.request('PUT', path, body);
    }

    delete(path) {
        return this.request('DELETE', path);
    }
}

export const api = new ApiClient();