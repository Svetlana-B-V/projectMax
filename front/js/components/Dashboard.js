import { analyticsApi } from '../api/analytics.js';
import { storage } from '../utils/storage.js';
import { formatCurrency, formatPercent } from '../utils/formatters.js';
import { drawDonutChart } from './DonutChart.js';
import { showLoading, showError, showEmptyState } from './UI.js';

export async function renderDashboard(container) {
    const group = storage.getActiveGroup();
    if (!group) {
        showEmptyState(container, 'Создайте или выберите группу');
        return;
    }

    showLoading(container);

    try {
        const [summary, mySummary, prediction] = await Promise.all([
            analyticsApi.getGroupSummary(group.id),
            analyticsApi.getMySummary(),
            analyticsApi.getPrediction(group.id),
        ]);

        const byCategory = summary.byCategory || {};
        const total = summary.total || 0;

        container.innerHTML = `
            <div class="welcome-section">
                <div>
                    <h1 class="welcome-title">Добрый день! 👋</h1>
                    <p class="welcome-subtitle">Группа: ${group.name}</p>
                </div>
                <button class="btn-primary btn-add" id="addExpenseBtn">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                        <path d="M12 5V19M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                    Добавить трату
                </button>
            </div>

            <div class="stats-grid">
                <div class="stat-card stat-card-green">
                    <div class="stat-icon">💰</div>
                    <div class="stat-content">
                        <p class="stat-label">Общие траты</p>
                        <p class="stat-value">${formatCurrency(total)}</p>
                        <p class="stat-change">${new Date().toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' })}</p>
                    </div>
                </div>

                <div class="stat-card stat-card-blue">
                    <div class="stat-icon">📊</div>
                    <div class="stat-content">
                        <p class="stat-label">Мои траты</p>
                        <p class="stat-value">${formatCurrency(mySummary.totalSpent || mySummary.total || 0)}</p>
                        <p class="stat-change">${mySummary.count || 0} операций</p>
                    </div>
                </div>

                <div class="stat-card stat-card-purple">
                    <div class="stat-icon">🎯</div>
                    <div class="stat-content">
                        <p class="stat-label">Прогноз на месяц</p>
                        <p class="stat-value">${formatCurrency(prediction.projectedTotal || 0)}</p>
                        <p class="stat-change">В среднем ${formatCurrency(prediction.dailyAvg || 0)}/день</p>
                    </div>
                </div>
            </div>

            <div class="dashboard-grid">
                <div class="card card-chart">
                    <div class="card-header">
                        <h2>Распределение расходов</h2>
                        <a href="analytics.html" class="btn-link">Подробнее →</a>
                    </div>
                    <div class="donut-container">
                        <canvas id="dashboardDonut" width="200" height="200"></canvas>
                        <div class="donut-legend" id="donutLegend"></div>
                    </div>
                </div>

                <div class="card card-actions">
                    <div class="card-header">
                        <h2>Быстрые действия</h2>
                    </div>
                    <div class="actions-grid">
                        <button class="action-btn" data-action="expense">
                            <div class="action-icon action-icon-green">💰</div>
                            <span>Добавить трату</span>
                        </button>
                        <button class="action-btn" data-action="report">
                            <div class="action-icon action-icon-blue">📊</div>
                            <span>Отчет</span>
                        </button>
                        <button class="action-btn" data-action="split">
                            <div class="action-icon action-icon-orange">🤝</div>
                            <span>Разделить счет</span>
                        </button>
                        <button class="action-btn" data-action="goal">
                            <div class="action-icon action-icon-purple">🎯</div>
                            <span>Цель</span>
                        </button>
                    </div>
                </div>
            </div>

            <div class="card card-transactions">
                <div class="card-header">
                    <h2>Последние операции</h2>
                    <a href="transactions.html" class="btn-link">Все операции →</a>
                </div>
                <div class="transactions-list" id="recentTransactions"></div>
            </div>
        `;

        // Кнопка добавления траты
        const addBtn = container.querySelector('#addExpenseBtn');
        if (addBtn) {
            addBtn.addEventListener('click', () => window.openAddExpenseModal());
        }

        // Быстрые действия
        container.querySelectorAll('.action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                if (btn.dataset.action === 'expense') {
                    window.openAddExpenseModal();
                } else {
                    window.open('https://t.me/obshchak_bot', '_blank');
                }
            });
        });

        // Donut chart
        const canvas = container.querySelector('#dashboardDonut');
        drawDonutChart(canvas, byCategory);

        // Легенда
        const legend = container.querySelector('#donutLegend');
        renderLegend(legend, byCategory);

        // Последние операции
        const recentList = container.querySelector('#recentTransactions');
        renderRecentTransactions(recentList, mySummary.recentExpenses || []);
    } catch (err) {
        showError(container, err.message);
    }
}

function renderLegend(container, byCategory) {
    if (!byCategory || Object.keys(byCategory).length === 0) {
        container.innerHTML = '<p class="empty-state">Нет данных</p>';
        return;
    }

    const colors = ['#21A038', '#00B578', '#FF6B6B', '#FFD93D', '#6C5CE7', '#4facfe', '#f093fb', '#43e97b'];
    const total = Object.values(byCategory).reduce((sum, val) => sum + val, 0);

    container.innerHTML = Object.entries(byCategory).map(([label, value], index) => {
        const percent = total > 0 ? (value / total) * 100 : 0;
        return `
            <div class="legend-item">
                <span class="legend-dot" style="background: ${colors[index % colors.length]}"></span>
                <div class="legend-content">
                    <span class="legend-label">${label}</span>
                    <span class="legend-value">${formatCurrency(value)}</span>
                </div>
                <span class="legend-percent">${formatPercent(percent)}</span>
            </div>
        `;
    }).join('');
}

function renderRecentTransactions(container, expenses) {
    if (!expenses || expenses.length === 0) {
        container.innerHTML = '<p class="empty-state">Нет операций</p>';
        return;
    }

    container.innerHTML = expenses.slice(0, 5).map(expense => `
        <div class="transaction-item">
            <div class="transaction-icon" style="background: ${expense.categoryColor || '#E8F5E9'}20">
                ${expense.categoryIcon || '💰'}
            </div>
            <div class="transaction-info">
                <p class="transaction-description">${expense.description || 'Без описания'}</p>
                <p class="transaction-meta">${expense.payer || ''} • ${new Date(expense.date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' })}</p>
            </div>
            <div class="transaction-amount negative">-${formatCurrency(expense.amount)}</div>
        </div>
    `).join('');
}