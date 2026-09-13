# CRM Kanban API - Контракты

## Базовый URL

`http://localhost:3000/api/v1`

## Формат ответов

### Успешный ответ
{

"data": { ... }

}

**Ошибка**

json

{

"message": "Описание ошибки",

"errors": null

}


**Аунтификация**
**POST /auth/register**

Регистрация нового пользователя.

**Тело запроса:**

json

{

"email": "string (обязательно, email)",

"password": "string (обязательно, мин. 6 символов)",

"role": "MANAGER | LEAD (опционально, по умолчанию MANAGER)"

}

**Успешный ответ (201):**

json

{

"user": {

"id": "string",

"email": "string",

"role": "string"

},

"accessToken": "string"

}

**Cookie:** Устанавливает refreshToken

**POST /auth/login**

Вход в систему.

**Тело запроса:**

json

{

"email": "string",

"password": "string"

}

**Успешный ответ (200):**

json

{

"user": {

"id": "string",

"email": "string",

"role": "string"

},

"accessToken": "string"

}

**Cookie:** Устанавливает refreshToken

**POST /auth/refresh**

Обновление токенов доступа.

**Cookie:** Требуется refreshToken

**Успешный ответ (200):**

json

{

"user": {

"id": "string",

"email": "string",

"role": "string"

},

"accessToken": "string"

}

**POST /auth/logout**

Выход из системы.

**Заголовки:**

text

Authorization: Bearer {accessToken}

**Успешный ответ (200):**

json

{

"ok": true

}

**Доски (Boards)**

**GET /boards**

Получить список доступных досок.

**Заголовки:**

text

Authorization: Bearer {accessToken}

**Успешный ответ (200):**

json

\[

{

"id": "string",

"title": "string",

"ownerId": "string",

"createdAt": "ISO дата",

"updatedAt": "ISO дата"

}

\]

**POST /boards**

Создать новую доску (только для LEAD).

**Заголовки:**

text

Authorization: Bearer {accessToken}

**Тело запроса:**

json

{

"title": "string (обязательно)"

}

**Успешный ответ (201):**

json

{

"id": "string",

"title": "string",

"ownerId": "string",

"createdAt": "ISO дата",

"updatedAt": "ISO дата"

}

**GET /boards/{id}**

Получить информацию о доске.

**Заголовки:**

text

Authorization: Bearer {accessToken}

**Успешный ответ (200):**

json

{

"id": "string",

"title": "string",

"ownerId": "string",

"createdAt": "ISO дата",

"updatedAt": "ISO дата"

}

**POST /boards/{id}/members**

Добавить участника в доску (только для LEAD).

**Заголовки:**

text

Authorization: Bearer {accessToken}

**Тело запроса:**

json

{

"userId": "string (обязательно, ID пользователя)"

}

**Успешный ответ (201):**

json

{

"id": "string",

"boardId": "string",

"userId": "string"

}

**Коды статусов**

- 200 - Успешно
- 201 - Создано
- 400 - Неверный запрос
- 401 - Не авторизован
- 403 - Запрещено (нет прав)
- 404 - Не найдено
- 500 - Внутренняя ошибка сервера
