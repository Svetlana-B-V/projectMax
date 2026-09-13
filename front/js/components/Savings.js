import { savingsApi } from '../api/savings.js';
import { storage } from '../utils/storage.js';
import { formatCurrency, formatPercent, formatDate } from '../utils/formatters.js';
import { showLoading, showError, showEmptyState } from './UI.js';

export async function renderSavings(container) {
    const group = storage.getActiveGroup();
    if (!group) {
        showEmptyState(container, 'Выберите группу');
        return;
    }

    showLoading(container);

    try {
        const goals = await savingsApi.getByGroup(group.id);

        container.innerHTML = `
            <div class="page-header">
                <div>
                    <h1 class="page-title">Копилки</h1>
                    <p class="page-subtitle">Цели накоплений группы «${group.name}»</p>
                </div>
                <button class="btn-primary btn-add" id="addSavingsBtn">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                        <path d="M12 5V19M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                    Создать копилку
                </button>
            </div>

            <div id="savingsFormContainer" class="hidden"></div>
            <div class="savings-grid" id="savingsList"></div>
        `;

        const savingsList = container.querySelector('#savingsList');
        renderSavingsList(savingsList, goals);

        container.querySelector('#addSavingsBtn').addEventListener('click', () => {
            showSavingsForm(container, group);
        });
    } catch (err) {
        showError(container, err.message);
    }
}

function renderSavingsList(container, goals) {
    if (!goals || goals.length === 0) {
        container.innerHTML = `
            <div class="empty-state-card">
                <div class="empty-icon">🏦</div>
                <h3>Нет копилок</h3>
                <p>Создайте первую копилку для накоплений</p>
            </div>
        `;
        return;
    }

    container.innerHTML = goals.map(goal => {
        const percent = goal.targetAmount > 0 ? (parseFloat(goal.currentAmount) / parseFloat(goal.targetAmount)) * 100 : 0;
        const remaining = Math.max(parseFloat(goal.targetAmount) - parseFloat(goal.currentAmount), 0);
        const isCompleted = percent >= 100;
        const isGroup = goal.type === 'group';

        return `
            <div class="savings-card">
                <div class="savings-card-header">
                    <div class="savings-icon" style="background: ${isGroup ? '#E8F5E9' : '#FFF3E0'}">
                        ${isGroup ? '👨‍👩‍👧' : '👤'}
                    </div>
                    <span class="savings-type ${isGroup ? 'type-group' : 'type-personal'}">
                        ${isGroup ? 'Семейная' : 'Личная'}
                    </span>
                </div>

                <h3 class="savings-name">${goal.name}</h3>

                <div class="progress-bar">
                    <div class="progress-fill ${isCompleted ? 'progress-completed' : ''}" style="width: ${Math.min(percent, 100)}%"></div>
                    <span class="progress-text">${formatPercent(percent)}</span>
                </div>

                <div class="savings-numbers">
                    <div>
                        <span class="savings-label">Собрано</span>
                        <span class="savings-current">${formatCurrency(goal.currentAmount)}</span>
                    </div>
                    <div class="savings-target">
                        <span class="savings-label">Цель</span>
                        <span class="savings-target-value">${formatCurrency(goal.targetAmount)}</span>
                    </div>
                </div>

                <div class="savings-footer">
                    ${isCompleted ?
            '<span class="savings-completed">🎉 Цель достигнута!</span>' :
            `<span class="savings-remaining">Осталось: ${formatCurrency(remaining)}</span>`
        }
                    ${goal.deadline ?
            `<span class="savings-deadline">📅 ${formatDate(goal.deadline)}</span>` :
            ''
        }
                </div>

                ${!isCompleted ? `
                    <button class="btn-contribute" data-goal-id="${goal.id}">
                        + Пополнить
                    </button>
                ` : ''}
            </div>
        `;
    }).join('');

    container.querySelectorAll('.btn-contribute').forEach(btn => {
        btn.addEventListener('click', () => {
            const goalId = btn.dataset.goalId;
            window.contributeToSavings(goalId);
        });
    });
}

function showSavingsForm(container, group) {
    const formContainer = container.querySelector('#savingsFormContainer');
    formContainer.classList.remove('hidden');
    formContainer.innerHTML = `
        <div class="savings-form-card">
            <h3>Новая копилка</h3>
            <form id="savingsForm">
                <div class="form-group">
                    <label>Название</label>
                    <input type="text" name="name" class="form-input" placeholder="Например: Отпуск" required>
                </div>
                <div class="form-group">
                    <label>Тип копилки</label>
                    <div class="type-selector">
                        <label class="type-option">
                            <input type="radio" name="type" value="group" checked>
                            <div class="type-option-content">
                                <span class="type-emoji">👨‍👩‍👧</span>
                                <span class="type-label">Семейная</span>
                                <span class="type-desc">Копят все участники</span>
                            </div>
                        </label>
                        <label class="type-option">
                            <input type="radio" name="type" value="personal">
                            <div class="type-option-content">
                                <span class="type-emoji">👤</span>
                                <span class="type-label">Личная</span>
                                <span class="type-desc">Только для себя</span>
                            </div>
                        </label>
                    </div>
                </div>
                <div class="form-group">
                    <label>Целевая сумма</label>
                    <input type="number" name="targetAmount" class="form-input" placeholder="100 000 ₽" required min="1">
                </div>
      
                <div class="savings-form-actions">
                    <button type="submit" class="btn-primary">Создать</button>
                    <button type="button" id="cancelSavingsBtn" class="btn-cancel">Отмена</button>
                </div>
            </form>
        </div>
    `;

    formContainer.querySelector('#cancelSavingsBtn').addEventListener('click', () => {
        formContainer.classList.add('hidden');
        formContainer.innerHTML = '';
    });

    formContainer.querySelector('#savingsForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);

        const data = {
            groupId: group.id,
            name: formData.get('name'),
            type: formData.get('type'),
            targetAmount: parseFloat(formData.get('targetAmount'))
        };

        try {
            await savingsApi.create(data);
            window.location.reload();
        } catch (err) {
            alert(err.message);
        }
    });
}

window.contributeToSavings = async function(goalId) {
    const amount = prompt('Сумма пополнения:');
    if (!amount) return;
    try {
        await savingsApi.contribute(goalId, parseFloat(amount));
        window.location.reload();
    } catch (err) {
        alert(err.message);
    }
};