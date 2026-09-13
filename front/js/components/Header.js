import { authApi } from '../api/auth.js';
import { storage } from '../utils/storage.js';

export function renderHeader(activePage = '') {
    const user = authApi.getUser();
    const userName = user?.name || 'Пользователь';

    const header = document.createElement('header');
    header.className = 'header';
    header.innerHTML = `
        <div class="header-logo">
            <img src="logo-sber.png" alt="Общак" class="logo">
            <span>Общак</span>
        </div>
        <nav class="header-nav">
            <a href="index.html" class="${activePage === 'dashboard' ? 'active' : ''}">Дашборд</a>
            <a href="transactions.html" class="${activePage === 'transactions' ? 'active' : ''}">Операции</a>
            <a href="savings.html" class="${activePage === 'savings' ? 'active' : ''}">Копилки</a>
            <a href="debts.html" class="${activePage === 'debts' ? 'active' : ''}">Долги</a>
            <a href="analytics.html" class="${activePage === 'analytics' ? 'active' : ''}">Аналитика</a>
        </nav>
        <div class="header-user">
            <span class="user-name">${userName}</span>
            <button id="logoutBtn" class="btn btn-outline">Выйти</button>
        </div>
    `;

    header.querySelector('#logoutBtn').addEventListener('click', () => {
        authApi.logout();
    });

    return header;
}