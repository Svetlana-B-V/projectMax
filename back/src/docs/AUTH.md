# Система аутентификации и авторизации

## Архитектура токенов

### Два типа токенов:

1\. **Access Token (JWT)**

\- Срок жизни: 15 минут

\- Передается в заголовке \`Authorization: Bearer {token}\`

\- Содержит: \`{ sub: userId, role: userRole, email: userEmail }\`

2\. **Refresh Token**

\- Срок жизни: 30 дней

\- Хранится в HTTP-only cookie

\- Используется для получения новой пары токенов

## Поток аутентификации

graph TD

A\[Пользователь вводит credentials\] --> B\[POST /auth/login\]

B --> C{Валидация}

C -->|Успех| D\[Генерация Access + Refresh токенов\]

D --> E\[Access Token в ответе, Refresh в cookie\]

E --> F\[Запросы с Access Token\]

F --> G{Access Token валиден?}

G -->|Да| H\[Выполнение запроса\]

G -->|Нет/Истек| I\[POST /auth/refresh\]

I --> J{Refresh Token валиден?}

J -->|Да| K\[Новая пара токенов\]

J -->|Нет| L\[401 Unauthorized\]

K --> F

**Механизм refresh токенов**

**Хранение:**

- Refresh токены хешируются с помощью bcrypt
- Хранятся в таблице RefreshToken
- Каждый токен привязан к пользователю

**Ротация токенов:**

1.  При использовании refresh токена, он помечается как использованный
2.  Выдается новый refresh токен
3.  Старый токен больше не может быть использован

**Безопасность:**

- HTTP-only cookies защищают от XSS
- SameSite=Lax защищает от CSRF
- Хеширование предотвращает утечку токенов из БД

**Роли и права доступа (RBAC)**

**Роли:**

- **LEAD** (Руководитель):
    - Создание новых досок
    - Добавление участников в доски
    - Полный доступ к своим доскам
- **MANAGER** (Менеджер):
    - Просмотр доступных досок
    - Работа с карточками (в будущем)
    - Комментирование (в будущем)

**Проверка прав на уровне middleware:**

javascript

_// Требуется аутентификация_

app.use('/boards', authMiddleware);

_// Требуется роль LEAD_

app.post('/boards', roleMiddleware(\['LEAD'\]));

_// Проверка доступа к конкретной доске_

app.get('/boards/:id', boardAccessMiddleware());

**Настройка cookies**

**Конфигурация refresh токена:**

javascript

res.cookie('refreshToken', token, {

httpOnly: true, _// Недоступен из JavaScript_

secure: process.env.COOKIE_SECURE === 'true', _// Только HTTPS_

sameSite: 'lax', _// Защита от CSRF_

path: '/api/v1/auth/refresh', _// Только для refresh endpoint_

maxAge: 30 \* 24 \* 60 \* 60 \* 1000 _// 30 дней_

});

**Для production:**

env

COOKIE_SECURE=true

COOKIE_DOMAIN=.yourdomain.com

**Защита от атак**

**1\. От утечки refresh токенов:**

- Хранение только хешей в БД
- Ограничение количества активных токенов на пользователя

**2\. От перехвата access токенов:**

- Короткое время жизни (15 минут)
- Нельзя обновить без valid refresh token

**3\. От CSRF:**

- SameSite cookies
- Отсутствие чувствительных операций через GET

**4\. От брутфорса:**

- bcrypt для паролей (стоимость 10)
- Лимиты запросов (можно добавить express-rate-limit)

**Отладка проблем**

**Common Issues:**

1.  **"No refresh token cookie"**

 Проверьте:

curl -v http://localhost:3000/api/v1/auth/refresh

# Должна быть строка: "Set-Cookie: refreshToken=..."

1.  **Access token истек**

javascript

_// Клиент должен обрабатывать 401_

try {

await api.getBoards();

} catch (error) {

if (error.status === 401) {

await refreshToken();

await api.getBoards(); _// Повтор запроса_

}

}

1.  **CORS проблемы**

javascript

_// В app.js_

app.use(cors({

origin: true, _// Разрешить все в dev_

credentials: true _// Важно для cookies_

}));

**Миграция с сессий на JWT**

Если вы переходите с session-based аутентификации:

1.  Замените сессии на JWT токены
2.  Реализуйте механизм refresh токенов
3.  Обновите клиентскую логику для обработки 401
4.  Добавьте автоматическое обновление токенов
