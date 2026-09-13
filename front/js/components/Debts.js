import { debtsApi } from '../api/debts.js';
import { formatCurrency } from '../utils/formatters.js';
import { showLoading, showError, showEmptyState } from './UI.js';

export async function renderDebts(container) {
    showLoading(container);

    try {
        const debts = await debtsApi.getMy();

        // Считаем суммы
        const myDebts = debts.filter(d => d.fromUserId === d.fromUserId); // Я должен
        const debtsToMe = debts.filter(d => d.toUserId !== d.fromUserId); // Мне должны

        const totalOwed = myDebts.reduce((sum, d) => sum + parseFloat(d.amount), 0);
        const totalOwedToMe = debtsToMe.reduce((sum, d) => sum + parseFloat(d.amount), 0);

        container.innerHTML = `
            <!-- Заголовок -->
            <div class="page-header">
                <div>
                    <h1 class="page-title">Долги</h1>
                    <p class="page-subtitle">Взаиморасчёты</p>
                </div>
            </div>

            <!-- Сводка -->
            <div class="debts-summary">
                <div class="debt-summary-card debt-owed">
                    <div class="debt-summary-icon">💸</div>
                    <h3>Я должен</h3>
                    <p class="amount negative">${formatCurrency(totalOwed)}</p>
                </div>
                <div class="debt-summary-card debt-receive">
                    <div class="debt-summary-icon">💰</div>
                    <h3>Мне должны</h3>
                    <p class="amount positive">${formatCurrency(totalOwedToMe)}</p>
                </div>
            </div>

            <!-- Список долгов -->
            <div class="debts-list" id="debtsList"></div>
        `;

        renderDebtsList(container.querySelector('#debtsList'), debts);
    } catch (err) {
        showError(container, err.message);
    }
}

function renderDebtsList(container, debts) {
    if (!debts || debts.length === 0) {
        container.innerHTML = `
            <div class="empty-state-card">
                <div class="empty-icon">🎉</div>
                <h3>Нет долгов</h3>
                <p>Все взаиморасчёты закрыты</p>
            </div>
        `;
        return;
    }

    container.innerHTML = debts.map(debt => {
        const isOwed = debt.fromUserId === debt.fromUserId; // Я должен
        const amount = parseFloat(debt.amount);
        const userName = debt.fromUser?.name || debt.toUser?.name || 'Неизвестно';
        const userInitial = userName.charAt(0).toUpperCase();

        return `
            <div class="debt-card ${isOwed ? 'debt-card-owed' : 'debt-card-receive'}">
                <div class="debt-avatar" style="background: ${getAvatarColor(userName)}">
                    ${userInitial}
                </div>
                <div class="debt-info">
                    <p class="debt-name">${userName}</p>
                    <p class="debt-status">${isOwed ? 'Вы должны' : 'Вам должны'}</p>
                </div>
                <div class="debt-actions">
                    <p class="debt-amount ${isOwed ? 'negative' : 'positive'}">
                        ${isOwed ? '-' : '+'}${formatCurrency(amount)}
                    </p>
                    ${isOwed ? `
                        <button class="btn-pay" data-debt-id="${debt.id}" data-max="${amount}">
                            Оплатить
                        </button>
                    ` : `
                        <button class="btn-remind" onclick="window.open('https://t.me/obshchak_bot', '_blank')">
                            Напомнить
                        </button>
                    `}
                </div>
            </div>
        `;
    }).join('');

    // Обработчики оплаты
    container.querySelectorAll('.btn-pay').forEach(btn => {
        btn.addEventListener('click', () => {
            const debtId = btn.dataset.debtId;
            const maxAmount = parseFloat(btn.dataset.max);
            window.payDebt(debtId, maxAmount);
        });
    });
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

window.payDebt = async function(debtId, maxAmount) {
    const amount = prompt(`Введите сумму (максимум ${maxAmount}):`);
    if (!amount) return;
    const numAmount = parseFloat(amount);
    if (numAmount <= 0 || numAmount > maxAmount) {
        alert('Некорректная сумма');
        return;
    }
    try {
        await debtsApi.pay(debtId, numAmount);
        window.location.reload();
    } catch (err) {
        alert(err.message);
    }
};