-- Локальное состояние бота. Бизнес-данные («Общак») живут в бэкенде, здесь только то,
-- что нужно самому боту.

CREATE TABLE IF NOT EXISTS user_sessions (
    telegram_id      INTEGER PRIMARY KEY,
    user_id          TEXT    NOT NULL,
    access_token     TEXT    NOT NULL,
    current_group_id TEXT,
    updated_at       TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Telegram-чат -> группа «Общака». invite_code хранится, чтобы участники чата
-- могли вступать в группу автоматически.
CREATE TABLE IF NOT EXISTS chat_groups (
    chat_id     INTEGER PRIMARY KEY,
    group_id    TEXT    NOT NULL,
    invite_code TEXT    NOT NULL,
    bound_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Кэш: кто из участников Telegram-чата уже состоит в привязанной группе.
CREATE TABLE IF NOT EXISTS chat_members (
    chat_id     INTEGER NOT NULL,
    telegram_id INTEGER NOT NULL,
    PRIMARY KEY (chat_id, telegram_id)
);

CREATE TABLE IF NOT EXISTS processed_updates (
    update_id    INTEGER PRIMARY KEY,
    processed_at TEXT NOT NULL DEFAULT (datetime('now'))
);
