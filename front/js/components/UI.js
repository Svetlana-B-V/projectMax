export function showLoading(container) {
    container.innerHTML = '<div class="loading">Загрузка...</div>';
}

export function showError(container, message) {
    container.innerHTML = `<div class="error-message">${message}</div>`;
}

export function showEmptyState(container, message) {
    container.innerHTML = `<div class="empty-state">${message}</div>`;
}

export function createButton(text, className = 'btn', onClick = null) {
    const btn = document.createElement('button');
    btn.className = className;
    btn.textContent = text;
    if (onClick) btn.addEventListener('click', onClick);
    return btn;
}

export function createModal(title, content, onClose = null) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
        <div class="modal">
            <div class="modal-header">
                <h3>${title}</h3>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">${content}</div>
        </div>
    `;

    overlay.querySelector('.modal-close').addEventListener('click', () => {
        overlay.remove();
        if (onClose) onClose();
    });

    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.remove();
            if (onClose) onClose();
        }
    });

    document.body.appendChild(overlay);
    return overlay;
}