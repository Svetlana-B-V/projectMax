import { analyticsApi } from '../api/analytics.js';
import { storage } from '../utils/storage.js';
import { formatCurrency, formatPercent } from '../utils/formatters.js';
import { drawDonutChart } from './DonutChart.js';
import { drawLineChart } from './LineChart.js';
import { showLoading, showError, showEmptyState } from './UI.js';

export async function renderAnalytics(container) {
    const group = storage.getActiveGroup();
    if (!group) {
        showEmptyState(container, 'Выберите группу');
        return;
    }

    showLoading(container);

    try {
        const [summary, mySummary, daily, prediction] = await Promise.all([
            analyticsApi.getGroupSummary(group.id),
            analyticsApi.getMySummary(),
            analyticsApi.getDaily(group.id),
            analyticsApi.getPrediction(group.id),
        ]);

        container.innerHTML = `
            <!-- Заголовок -->
            <div class="page-header">
                <div>
                    <h1 class="page-title">Аналитика</h1>
                    <p class="page-subtitle">Детальный анализ трат группы «${group.name}»</p>
                </div>
            </div>

            <!-- Статистика -->
            <div class="stats-grid">
                <div class="stat-card stat-card-green">
                    <div class="stat-icon">💰</div>
                    <div class="stat-content">
                        <p class="stat-label">Всего потрачено</p>
                        <p class="stat-value">${formatCurrency(summary.total || 0)}</p>
                        <p class="stat-change">За текущий месяц</p>
                    </div>
                </div>

                <div class="stat-card stat-card-blue">
                    <div class="stat-icon">📈</div>
                    <div class="stat-content">
                        <p class="stat-label">Прогноз на месяц</p>
                        <p class="stat-value">${formatCurrency(prediction.projectedTotal || 0)}</p>
                        <p class="stat-change">В среднем ${formatCurrency(prediction.dailyAvg || 0)}/день</p>
                    </div>
                </div>

                <div class="stat-card stat-card-purple">
                    <div class="stat-icon">👤</div>
                    <div class="stat-content">
                        <p class="stat-label">Мои траты</p>
                        <p class="stat-value">${formatCurrency(mySummary.totalSpent || mySummary.total || 0)}</p>
                        <p class="stat-change">${mySummary.count || 0} операций</p>
                    </div>
                </div>
            </div>

            <!-- Графики -->
            <div class="analytics-charts-grid">
                <div class="card chart-card">
                    <div class="card-header">
                        <h2>Сводка по группе</h2>
                    </div>
                    <div class="chart-donut-container">
                        <canvas id="groupDonut" width="250" height="250"></canvas>
                        <div class="donut-legend" id="groupLegend"></div>
                    </div>
                </div>

                <div class="card chart-card">
                    <div class="card-header">
                        <h2>Мои траты</h2>
                    </div>
                    <div class="chart-donut-container">
                        <canvas id="myDonut" width="250" height="250"></canvas>
                        <div class="donut-legend" id="myLegend"></div>
                    </div>
                </div>

                <div class="card chart-card analytics-wide">
                    <div class="card-header">
                        <h2>Динамика по дням</h2>
                    </div>
                    <div class="line-chart-container">
                        <canvas id="dailyChart" width="800" height="300"></canvas>
                    </div>
                </div>

                <div class="card prediction-card">
                    <div class="card-header">
                        <h2>Прогноз</h2>
                    </div>
                    <div class="prediction-content">
                        <div class="prediction-main">
                            <span class="prediction-label">Прогноз на месяц</span>
                            <span class="prediction-value">${formatCurrency(prediction.projectedTotal || 0)}</span>
                        </div>
                        <div class="prediction-details">
                            <div class="prediction-item">
                                <span>Потрачено</span>
                                <strong>${formatCurrency(prediction.totalSpent || 0)}</strong>
                            </div>
                            <div class="prediction-item">
                                <span>Среднее в день</span>
                                <strong>${formatCurrency(prediction.dailyAvg || 0)}</strong>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Рисуем графики
        drawDonutChart(container.querySelector('#groupDonut'), summary.byCategory || {});
        drawDonutChart(container.querySelector('#myDonut'), mySummary.byCategory || {});
        drawLineChart(container.querySelector('#dailyChart'), daily || {});

        // Легенды
        renderLegend(container.querySelector('#groupLegend'), summary.byCategory || {});
        renderLegend(container.querySelector('#myLegend'), mySummary.byCategory || {});
    } catch (err) {
        showError(container, err.message);
    }
}

function renderLegend(container, data) {
    if (!container) return;

    if (!data || Object.keys(data).length === 0) {
        container.innerHTML = '<p class="empty-state">Нет данных</p>';
        return;
    }

    const colors = ['#21A038', '#00B578', '#FF6B6B', '#FFD93D', '#6C5CE7', '#4facfe', '#f093fb', '#43e97b'];
    const total = Object.values(data).reduce((sum, val) => sum + val, 0);

    container.innerHTML = Object.entries(data).map(([label, value], index) => {
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