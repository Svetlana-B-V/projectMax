import { expensesApi } from '../api/expenses.js';
import { categoriesApi } from '../api/categories.js';
import { storage } from '../utils/storage.js';
import { formatCurrency, formatDate } from '../utils/formatters.js';
import { showLoading, showError, showEmptyState } from './UI.js';

export async function renderTransactions(container) {
    const group = storage.getActiveGroup();
    if (!group) {
        showEmptyState(container, 'Создайте или выберите группу');
        return;
    }

    showLoading(container);

    try {
        const [expenses, categories] = await Promise.all([
            expensesApi.getByGroup(group.id),
            categoriesApi.getAll(group.id),
        ]);

        container.innerHTML = `
            <div class="page-header">
                <div>
                    <h1 class="page-title">Операции</h1>
                    <p class="page-subtitle">Все траты группы «${group.name}»</p>
                </div>
                <button class="btn-primary btn-add" id="addExpenseBtn">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                        <path d="M12 5V19M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                    Добавить трату
                </button>
            </div>

            <div class="filters-card">
                <div class="filters-row">
                    <div class="filter-group">
                        <label>Категория</label>
                        <select id="categoryFilter" class="filter-select">
                            <option value="">Все категории</option>
                            ${categories.map(cat => `
                                <option value="${cat.id}">${cat.icon || ''} ${cat.name}</option>
                            `).join('')}
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>Период</label>
                        <select id="periodFilter" class="filter-select">
                            <option value="month">Текущий месяц</option>
                            <option value="week">Эта неделя</option>
                            <option value="today">Сегодня</option>
                            <option value="all">Всё время</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>Сортировка</label>
                        <select id="sortFilter" class="filter-select">
                            <option value="new">Сначала новые</option>
                            <option value="old">Сначала старые</option>
                            <option value="amount">По сумме</option>
                        </select>
                    </div>
                </div>
            </div>

            <div class="transactions-container">
                <div class="transactions-list" id="transactionsList"></div>
            </div>
        `;

        // Кнопка добавления
        const addBtn = container.querySelector('#addExpenseBtn');
        if (addBtn) {
            addBtn.addEventListener('click', () => window.openAddExpenseModal());
        }

        const list = container.querySelector('#transactionsList');
        renderTransactionsList(list, expenses);

        setupFilters(container, expenses);
    } catch (err) {
        showError(container, err.message);
    }
}

function renderTransactionsList(container, expenses) {
    if (!expenses || expenses.length === 0) {
        container.innerHTML = `
            <div class="empty-state-card">
                <div class="empty-icon">📭</div>
                <h3>Нет операций</h3>
                <p>Добавьте первую трату через Telegram-бота</p>
            </div>
        `;
        return;
    }

    container.innerHTML = expenses.map(expense => `
        <div class="transaction-card">
            <div class="transaction-icon" style="background: ${expense.categoryColor || '#E8F5E9'}20">
                ${expense.categoryIcon || '💰'}
            </div>
            <div class="transaction-info">
                <p class="transaction-description">${expense.description || 'Без описания'}</p>
                <p class="transaction-meta">
                    ${expense.payer || 'Неизвестно'} • ${formatDate(expense.date)}
                    ${expense.categoryName ? ` • ${expense.categoryName}` : ''}
                </p>
            </div>
            <div class="transaction-actions">
                <p class="transaction-amount negative">-${formatCurrency(expense.amount)}</p>
            </div>
        </div>
    `).join('');
}

function setupFilters(container, expenses) {
    const categoryFilter = container.querySelector('#categoryFilter');
    const periodFilter = container.querySelector('#periodFilter');
    const sortFilter = container.querySelector('#sortFilter');
    const list = container.querySelector('#transactionsList');

    function applyFilters() {
        let filtered = [...expenses];

        if (categoryFilter.value) {
            filtered = filtered.filter(e => e.categoryId === categoryFilter.value);
        }

        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
        const monthAgo = new Date(now.getFullYear(), now.getMonth(), 1);

        switch (periodFilter.value) {
            case 'today':
                filtered = filtered.filter(e => new Date(e.date) >= today);
                break;
            case 'week':
                filtered = filtered.filter(e => new Date(e.date) >= weekAgo);
                break;
            case 'month':
                filtered = filtered.filter(e => new Date(e.date) >= monthAgo);
                break;
        }

        switch (sortFilter.value) {
            case 'old':
                filtered.sort((a, b) => new Date(a.date) - new Date(b.date));
                break;
            case 'amount':
                filtered.sort((a, b) => b.amount - a.amount);
                break;
            default:
                filtered.sort((a, b) => new Date(b.date) - new Date(a.date));
        }

        renderTransactionsList(list, filtered);
    }

    categoryFilter.addEventListener('change', applyFilters);
    periodFilter.addEventListener('change', applyFilters);
    sortFilter.addEventListener('change', applyFilters);
}