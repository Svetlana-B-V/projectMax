# Настройка проекта

## Требования

\- Node.js 18+

\- Docker и Docker Compose

\- PostgreSQL (через Docker)

## Установка

1\. **Клонирование и установка зависимостей**

npm install

1.  **Настройка переменных окружения**



cp .env.example .env

Отредактируйте .env при необходимости.

1.  **Запуск базы данных**


docker-compose up -d

1.  **Применение миграций Prisma**


npx prisma migrate dev --name init

1.  **Генерация Prisma клиента**



npx prisma generate

1.  **Запуск сервера**



_\# Development режим_

npm run dev

_\# Production режим_

npm run build

npm start

**Проверка работоспособности**

1.  **Проверка здоровья API**


curl http://localhost:3000/health

**Ожидаемый ответ:** {"ok": true}

1.  **Проверка базы данных**


_\# Подключение к PostgreSQL_

docker exec -it crm_kanban_db psql -U postgres -d crm_kanban

**Тестовые данные**

**Создание тестовых пользователей через Prisma Studio**


npx prisma studio

Или через миграцию:


INSERT INTO "User" (id, email, "passwordHash", role)

VALUES

('user_lead_1', 'lead@company.com', '$2a$10$...', 'LEAD'),

('user_manager_1', 'manager@company.com', '$2a$10$...', 'MANAGER');

**Переменные окружения (.env)**

env

\# База данных

DATABASE_URL="postgresql://postgres:postgres@localhost:5432/crm_kanban?schema=public"

\# JWT

JWT_ACCESS_SECRET="super_secret_access_key_123"

JWT_REFRESH_SECRET="super_secret_refresh_key_456"

\# Токены

ACCESS_TOKEN_EXPIRES_IN="15m"

REFRESH_TOKEN_EXPIRES_IN_DAYS="30"

\# Cookies

COOKIE_SECURE="false"

COOKIE_DOMAIN=""

\# Порт сервера

PORT="3000"

**Структура базы данных**

**Основные таблицы:**

- User - Пользователи
- RefreshToken - Токены обновления
- Board - Доски проектов
- BoardMember - Участники досок
- Column - Колонки на досках
- Card - Карточки задач
- Comment - Комментарии к карточкам

Просмотр схемы: prisma/schema.prisma
