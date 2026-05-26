# Архитектура — Информационный портал кафедры

## Стек

- Python 3.11+, FastAPI, PostgreSQL, SQLAlchemy 2.0 async
- JWT (access + refresh) через python-jose
- Файлы: локальная ФС `/uploads`
- Email: Resend API (`httpx`)
- Админ-панель: sqladmin

---

## Структура проекта

```
app/
├── admin/          — sqladmin: auth.py, views.py
├── alembic/        — миграции
├── announcements/  — объявления
├── attendance/     — посещаемость
├── auth/           — аутентификация, JWT
├── chat/           — чаты (WebSocket + REST)
├── core/           — config, email, security, file_storage
├── db/             — base, session, models (импорт всех моделей для Alembic)
├── dependencies.py — get_current_user, require_roles
├── documents/      — документы
├── events/         — мероприятия
├── groups/         — группы
├── lessons/        — занятия
├── main.py         — точка входа, монтирование роутеров
├── notifications/  — уведомления
├── rooms/          — аудитории
├── streams/        — потоки
├── users/          — пользователи, профили
└── vkr/            — темы ВКР
```

---

## Аутентификация

- `POST /api/v1/auth/register` — самостоятельная регистрация студента
- `POST /api/v1/auth/login` — вход (OAuth2 form), возвращает access + refresh токены
- `POST /api/v1/auth/refresh` — обновление токенов
- `POST /api/v1/auth/logout` — отзыв refresh-токена
- `POST /api/v1/auth/reset-password` — сброс пароля, новый отправляется на email
- `GET /api/v1/auth/me` — текущий пользователь

**Bearer-схема:** `HTTPBearer` (не OAuth2PasswordBearer). Токен передаётся в заголовке `Authorization: Bearer <token>`.

Refresh-токены хранятся в таблице `refresh_tokens` (jti, revoked, expires_at).

---

## Роли пользователей

| Роль | Описание |
|------|----------|
| `student` | Студент — регистрируется сам |
| `headman` | Староста — создаётся админом |
| `teacher` | Преподаватель — создаётся админом |
| `deputy_head` | Зав. кафедрой — создаётся админом |
| `dean` | Деканат — создаётся админом |
| `admin` | Администратор |

---

## Пользователи и профили

### Создание пользователей

**Студент** регистрируется сам через `POST /auth/register` (схема `StudentRegister`):
```json
{ "name", "surname", "patronymic"?, "email", "password", "group_id" }
```

**Все остальные роли** создаются администратором через `POST /users` (схема `UserCreate`):
```json
{ "name", "surname", "patronymic"?, "email", "role", "group_id"? }
```
Пароль для headman, teacher, deputy_head, dean генерируется автоматически и отправляется на email.

### Профили

При создании пользователя автоматически создаётся запись профиля по роли:

| Роль | Таблица | Поля |
|------|---------|------|
| student, headman | `student_profiles` | group_id, phone, telegram, vk |
| teacher, deputy_head | `teacher_profiles` | department, positions, phone, cabinet |
| dean | `dean_profiles` | faculty (default ""), position, phone, cabinet |

### Обновление профиля

Каждый пользователь обновляет свой профиль сам. Эндпоинты проверяют роль:

- `PATCH /users/me/student-profile` — только student, headman
- `PATCH /users/me/teacher-profile` — только teacher, deputy_head
- `PATCH /users/me/dean-profile` — только dean

### Прочие эндпоинты пользователей

- `GET /users` — список пользователей (видимость зависит от роли)
- `GET /users/teachers` — все преподаватели и зав. кафедрой без телефона (для авторизованных)
- `GET /users/search?surname=` — поиск по фамилии
- `PUT /users/{id}` — обновление базовых данных (ФИО, email)
- `PATCH /users/{id}/password` — смена пароля
- `PATCH /users/me/avatar` — загрузка аватарки
- `GET /users/{id}/avatar` — получение аватарки
- `DELETE /users/{id}` — удаление (только admin)

### Видимость пользователей (`GET /users`)

| Роль | Видит |
|------|-------|
| admin, dean, deputy_head | Всех |
| student, headman | Одногруппников + всех преподавателей |
| teacher | Студентов своих групп + deputy_head |

---

## Чат

Модуль `app/chat/`. Заменил старый модуль `messages`.

**Типы чатов:** `direct` (личный), `group` (групповой).

**Эндпоинты:**
- `GET /chats` — список чатов (admin видит все, остальные — свои)
- `POST /chats/group` — создать групповой чат
- `GET /chats/direct/{user_id}` — получить или создать личный чат
- `GET /chats/{id}/messages` — история сообщений
- `POST /chats/{id}/messages` — отправить сообщение через REST
- `WS /chats/{id}/ws` — WebSocket для реального времени

**Таблицы:** `chats`, `chat_members`, `chat_messages`.

---

## ВКР

Модуль `app/vkr/`. Таблица `vkr_topics`.

**Статусы:** `pending` → `approved` / `rejected`

**Эндпоинты:**
- `POST /vkr/topics` — предложить тему (student, headman, teacher)
- `GET /vkr/my-topics` — мои темы
- `GET /vkr/topics` — все темы с фильтром по статусу (deputy_head, admin)
- `GET /vkr/topics/approved` — одобренные (dean, deputy_head, admin)
- `GET /vkr/topics/{id}` — детали темы
- `POST /vkr/topics/{id}/review` — одобрить/отклонить (deputy_head)

При отклонении комментарий обязателен.

---

## Объявления

- `GET /announcements` — список (фильтрация по роли пользователя)
- `GET /announcements/my` — объявления текущего пользователя
- `POST /announcements` — создать
- `PUT /announcements/{id}` — обновить
- `DELETE /announcements/{id}` — удалить (soft delete)
- `POST /announcements/{id}/restore` — восстановить

---

## Email

`app/core/email.py`. Внутренний хелпер `_send_email` используется двумя функциями:
- `send_credentials_email` — отправка логина/пароля при создании пользователя
- `send_password_reset_email` — отправка нового пароля при сбросе

Требует `RESEND_API_KEY` в `.env`. При отсутствии — логирует предупреждение и пропускает.

---

## Административная панель

URL: `http://localhost:8000/admin`
Вход: email + пароль пользователя с ролью `admin`

**Представления:** UserAdmin, RefreshTokenAdmin, StreamAdmin, GroupAdmin, ChatAdmin, ChatMessageAdmin, EventAdmin, DocumentAdmin

---

## CI/CD

`.gitlab-ci.yml` — три стадии: build → test → deploy.
Deploy только из ветки `main`, через SSH на сервер.

---

## Миграции

```bash
docker compose exec api alembic upgrade head
```

Актуальная цепочка миграций:
- `49db932424b1` — начальные таблицы
- `b3c4d5e6f7a8` — замена messages на chat
- `aa3f86f1e167` — announcement_id nullable в events
- `f1a2b3c4d5e6` — роль deputy_head
- `019304363317` — таблица vkr_topics
