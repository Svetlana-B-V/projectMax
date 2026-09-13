# Примеры использования API

## Использование cURL
### 1. Полный сценарий регистрации и работы

#!/bin/bash

BASE_URL="http://localhost:3000/api/v1"

# 1. Регистрация LEAD

echo "1. Регистрация LEAD пользователя..."

REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \\

\-H "Content-Type: application/json" \\

\-d '{

"email": "project.lead@example.com",

"password": "LeadPass123",

"role": "LEAD"

}')

echo "$REGISTER_RESPONSE"

ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"accessToken":"\[^"\]\*' | cut -d'"' -f4)

echo "Access Token получен"

\# 2. Создание доски

echo "\\n2. Создание доски проекта..."

BOARD_RESPONSE=$(curl -s -X POST "$BASE_URL/boards" \\

\-H "Content-Type: application/json" \\

\-H "Authorization: Bearer $ACCESS_TOKEN" \\

\-d '{

"title": "Проект разработки API"

}')

echo "$BOARD_RESPONSE"

BOARD_ID=$(echo "$BOARD_RESPONSE" | grep -o '"id":"\[^"\]\*' | cut -d'"' -f4)

\# 3. Получение списка досок

echo "\\n3. Получение списка доступных досок..."

curl -X GET "$BASE_URL/boards" \\

\-H "Authorization: Bearer $ACCESS_TOKEN"

**2\. Пример с сохранением cookies**

bash

_\# Сохраняем cookies в файл_

curl -X POST "http://localhost:3000/api/v1/auth/login" \\

\-H "Content-Type: application/json" \\

\-d '{"email":"user@example.com","password":"password123"}' \\

\-c cookies.txt

_\# Используем cookies для refresh_

curl -X POST "http://localhost:3000/api/v1/auth/refresh" \\

\-b cookies.txt \\

\-c cookies.txt

**Использование с JavaScript (Fetch API)**

**1\. Класс для работы с API**

javascript

class KanbanAPI {

constructor(baseUrl = 'http://localhost:3000/api/v1') {

this.baseUrl = baseUrl;

this.accessToken = null;

}

async login(email, password) {

const response = await fetch(\`${this.baseUrl}/auth/login\`, {

method: 'POST',

headers: { 'Content-Type': 'application/json' },

body: JSON.stringify({ email, password }),

credentials: 'include' _// важно для cookies_

});

const data = await response.json();

this.accessToken = data.accessToken;

return data;

}

async getBoards() {

const response = await fetch(\`${this.baseUrl}/boards\`, {

method: 'GET',

headers: {

'Authorization': \`Bearer ${this.accessToken}\`

}

});

return response.json();

}

async createBoard(title) {

const response = await fetch(\`${this.baseUrl}/boards\`, {

method: 'POST',

headers: {

'Content-Type': 'application/json',

'Authorization': \`Bearer ${this.accessToken}\`

},

body: JSON.stringify({ title })

});

return response.json();

}

async refreshToken() {

const response = await fetch(\`${this.baseUrl}/auth/refresh\`, {

method: 'POST',

credentials: 'include' _// отправляем cookies_

});

const data = await response.json();

this.accessToken = data.accessToken;

return data;

}

}

_// Использование_

const api = new KanbanAPI();

await api.login('user@example.com', 'password123');

const boards = await api.getBoards();

console.log(boards);

**2\. Обработка ошибок**

javascript

async function apiCall(url, options = {}) {

try {

const response = await fetch(url, options);

if (!response.ok) {

const error = await response.json();

throw new Error(error.message || \`HTTP ${response.status}\`);

}

return await response.json();

} catch (error) {

console.error('API Error:', error);

_// Здесь можно добавить логику для refresh token_

if (error.message.includes('401')) {

_// Попробовать обновить токен_

}

throw error;

}

}

**Использование с Postman**

**Коллекция Postman**

1.  **Создайте новую коллекцию:** "CRM Kanban API"
2.  **Добавьте переменные:**

json

{

"base_url": "http://localhost:3000/api/v1",

"access_token": "",

"board_id": ""

}

1.  **Запросы:**
    - POST {{base_url}}/auth/login
    - POST {{base_url}}/auth/register
    - GET {{base_url}}/boards
    - POST {{base_url}}/boards
2.  **Тесты (для автоматизации):**

javascript

_// После логина_

pm.test("Status code is 200", function () {

pm.response.to.have.status(200);

});

pm.test("Response has access token", function () {

const jsonData = pm.response.json();

pm.expect(jsonData.accessToken).to.be.a('string');

pm.collectionVariables.set("access_token", jsonData.accessToken);

});

**Тестовые данные**

**Для быстрого тестирования:**

bash

_\# 1. Создайте тестового пользователя_

curl -X POST "http://localhost:3000/api/v1/auth/register" \\

\-H "Content-Type: application/json" \\

\-d '{"email":"test@test.com","password":"test123","role":"LEAD"}'

_\# 2. Используйте для всех последующих запросов_

Authorization: Bearer ваш_токен

**Сценарий "Первый запуск":**

1.  Запустите сервер
2.  Выполните регистрацию LEAD
3.  Создайте первую доску
4.  Пригласите MANAGER
5.  Проверьте доступ с двух аккаунтов

text

\---
