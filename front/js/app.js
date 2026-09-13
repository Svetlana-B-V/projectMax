import { authApi } from './api/auth.js';
import { groupsApi } from './api/groups.js';
import { expensesApi } from './api/expenses.js';
import { categoriesApi } from './api/categories.js';
import { storage } from './utils/storage.js';
import { renderDashboard } from './components/Dashboard.js';
import { renderTransactions } from './components/Transactions.js';
import { renderSavings } from './components/Savings.js';
import { renderDebts } from './components/Debts.js';
import { renderAnalytics } from './components/Analytics.js';

// ============ МОДАЛКА ============
function openAddExpenseModal() {
    let modal = document.getElementById('modal');

    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'modal';
        document.body.appendChild(modal);
    }

    const group = storage.getActiveGroup();

    categoriesApi.getAll(group?.id).then(categories => {
        modal.innerHTML = `
            <div class="modal-overlay" id="modalOverlay">
                <div class="modal-content" id="modalContent">
                    <div class="modal-header">
                        <h3>Добавить трату</h3>
                        <button class="modal-close" id="modalCloseBtn">✕</button>
                    </div>
                    <div class="modal-body">
                        <form id="addExpenseForm">
                            <div class="form-group">
                                <label>Сумма</label>
                                <input type="number" id="expenseAmount" class="form-input" placeholder="0 ₽" required min="1" step="0.01">
                            </div>
                            <div class="form-group">
                                <label>Описание</label>
                                <input type="text" id="expenseDescription" class="form-input" placeholder="Например: Обед в кафе" required>
                            </div>
                            <div class="form-group">
                                <label>Категория</label>
                                <select id="expenseCategory" class="form-input" required>
                                    <option value="">Выберите категорию</option>
                                    ${categories.map(cat => `
                                        <option value="${cat.id}">${cat.icon || ''} ${cat.name}</option>
                                    `).join('')}
                                </select>
                            </div>
                            <button type="submit" class="btn-primary full-width">Добавить</button>
                        </form>
                    </div>
                </div>
            </div>
        `;

        document.getElementById('modalOverlay').addEventListener('click', closeModal);
        document.getElementById('modalContent').addEventListener('click', (e) => e.stopPropagation());
        document.getElementById('modalCloseBtn').addEventListener('click', closeModal);
        document.getElementById('addExpenseForm').addEventListener('submit', addExpense);
    });
}

function closeModal() {
    const modal = document.getElementById('modal');
    if (modal) {
        modal.innerHTML = '';
    }
}

async function addExpense(event) {
    event.preventDefault();

    const group = storage.getActiveGroup();
    const user = authApi.getUser();

    const amount = parseFloat(document.getElementById('expenseAmount').value);
    const description = document.getElementById('expenseDescription').value;
    const categoryId = document.getElementById('expenseCategory').value;

    if (!group || !user) {
        alert('Не выбрана группа или вы не авторизованы');
        return;
    }

    try {
        await expensesApi.create({
            groupId: group.id,
            payerId: user.id,
            categoryId: categoryId,
            amount: amount,
            description: description
        });

        closeModal();
        alert('✅ Трата добавлена!');
        location.reload();
    } catch (err) {
        alert('❌ Ошибка: ' + err.message);
    }
}

window.openAddExpenseModal = openAddExpenseModal;

// ============ ИНИЦИАЛИЗАЦИЯ ============
async function initApp() {
    const path = window.location.pathname;

    if (path.includes('login.html')) {
        initLoginPage();
        return;
    }

    if (!authApi.isAuthenticated()) {
        window.location.href = 'login.html';
        return;
    }

    try {
        const groups = await groupsApi.getMyGroups();
        if (groups.length > 0) {
            let activeGroup = storage.getActiveGroup();
            if (!activeGroup || !groups.find(g => g.id === activeGroup.id)) {
                activeGroup = groups[0];
                storage.setActiveGroup(activeGroup);
            }
        }
    } catch (err) {
        console.error('Ошибка загрузки групп:', err);
    }

    updateAvatar();

    const mainContainer = document.getElementById('main');
    if (!mainContainer) return;

    if (path.includes('index.html') || path === '/' || path.endsWith('/')) {
        await renderDashboard(mainContainer);
    } else if (path.includes('transactions.html')) {
        await renderTransactions(mainContainer);
    } else if (path.includes('savings.html')) {
        await renderSavings(mainContainer);
    } else if (path.includes('debts.html')) {
        await renderDebts(mainContainer);
    } else if (path.includes('analytics.html')) {
        await renderAnalytics(mainContainer);
    } else if (path.includes('profile.html')) {
        renderProfile(mainContainer);
    }
}

function updateAvatar() {
    const user = authApi.getUser();
    const avatarText = document.getElementById('avatarText');
    if (avatarText && user?.name) {
        avatarText.textContent = user.name.charAt(0).toUpperCase();
    }
}

function initLoginPage() {
    const loginForm = document.getElementById('loginForm');

    loginForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const telegramId = document.getElementById('loginEmail').value;
        const name = document.getElementById('loginPassword').value || 'Пользователь';

        if (!telegramId) {
            alert('Введите Telegram ID');
            return;
        }

        try {
            await authApi.loginByTelegram(parseInt(telegramId), name);
            window.location.href = 'index.html';
        } catch (err) {
            alert(err.message || 'Ошибка входа');
        }
    });
}

function renderProfile(container) {
    const user = authApi.getUser();
    if (!user) {
        window.location.href = 'login.html';
        return;
    }

    const userInitial = user.name ? user.name.charAt(0).toUpperCase() : '?';
    const avatarColor = getAvatarColor(user.name || '');

    container.innerHTML = `
        <div class="page-header">
            <div>
                <h1 class="page-title">Профиль</h1>
                <p class="page-subtitle">Личные данные</p>
            </div>
        </div>

        <div class="profile-container">
            <div class="profile-card">
                <div class="profile-cover"></div>
                <div class="profile-avatar-large" style="background: ${avatarColor}">
                    ${userInitial}
                </div>
                
                <h2 class="profile-name">${user.name || 'Пользователь'}</h2>
                <p class="profile-email">${user.email || ''}</p>
                
                ${user.telegramId ? `
                    <div class="profile-telegram">
                        <span>📱 Telegram:</span>
                        <strong>${user.telegramId}</strong>
                    </div>
                ` : `
                    <div class="profile-telegram not-linked">
                        <span>📱 Telegram не привязан</span>
                    </div>
                `}

                <div class="profile-divider"></div>

                <div class="profile-stats-grid">
                    <div class="profile-stat-card">
                        <div class="profile-stat-icon">💰</div>
                        <span class="profile-stat-label">Баланс</span>
                        <span class="profile-stat-value">+5 600 ₽</span>
                    </div>
                    <div class="profile-stat-card">
                        <div class="profile-stat-icon">💸</div>
                        <span class="profile-stat-label">Долги</span>
                        <span class="profile-stat-value negative">-3 200 ₽</span>
                    </div>
                    <div class="profile-stat-card">
                        <div class="profile-stat-icon">🏦</div>
                        <span class="profile-stat-label">Копилки</span>
                        <span class="profile-stat-value">3</span>
                    </div>
                </div>

                <div class="profile-divider"></div>

                <div class="profile-actions">
                    <button class="btn-telegram" onclick="window.open('https://t.me/obshchak_bot', '_blank')">
                        Привязать Telegram
                    </button>
                    <button class="btn-logout" id="logoutBtn">
                        Выйти
                    </button>
                </div>
            </div>
        </div>
    `;

    // Обработчик выхода
    const logoutBtn = container.querySelector('#logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            authApi.logout();
            window.location.href = 'login.html';
        });
    }
}

function getAvatarColor(name) {
    const colors = [
        'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
        'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
        'linear-gradient(135deg, #30cfd0 0%, #330867 100%)'
    ];

    let hash = 0;
    for (let i = 0; i < name.length; i++) {
        hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }

    return colors[Math.abs(hash) % colors.length];
}

document.addEventListener('DOMContentLoaded', initApp);