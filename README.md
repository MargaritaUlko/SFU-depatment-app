# Department Portal API

REST API информационного портала кафедры. Дипломный проект.

## Стек

| Слой | Технология |
|------|------------|
| Язык | Python 3.11+ |
| Фреймворк | FastAPI |
| СУБД | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Миграции | Alembic |
| Auth | JWT (access + refresh) via python-jose |
| Файлы | Локальная ФС (`/uploads`) |

## Быстрый старт (Docker Compose)

```bash
# 1. Скопировать переменные окружения
cp .env.example .env

# 2. Поднять контейнеры (PostgreSQL + API)
docker compose up --build -d

# 3. Применить миграции
docker compose exec api alembic upgrade head

# 4. Открыть Swagger UI
open http://localhost:8000/docs
```

## Локальный запуск (без Docker)

```bash
# 1. Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Настроить .env (DATABASE_URL, SECRET_KEY, ...)
cp .env.example .env

# 4. Применить миграции
alembic upgrade head

# 5. Запустить сервер
uvicorn app.main:app --reload
```

## API

Swagger UI: http://localhost:8000/docs  
ReDoc:       http://localhost:8000/redoc

### Префикс всех эндпоинтов: `/api/v1/`

| Метод | Путь | Описание | Роли |
|-------|------|----------|------|
| POST | /auth/register | Регистрация | — |
| POST | /auth/login | Вход | — |
| POST | /auth/refresh | Обновление токена | — |
| POST | /auth/logout | Выход | — |
| GET | /users | Список пользователей | head, admin |
| GET | /users/{id} | Профиль | авторизован |
| PUT | /users/{id} | Обновление профиля | сам / admin |
| PATCH | /users/{id}/role | Смена роли | admin |
| DELETE | /users/{id} | Удаление | admin |
| GET | /groups | Список групп | авторизован |
| POST | /groups | Создать группу | admin |
| GET | /streams | Список потоков | авторизован |
| POST | /streams | Создать поток | admin |
| POST | /messages | Отправить сообщение | teacher, head, admin |
| GET | /messages | История сообщений | teacher, head, admin |
| GET | /messages/{id} | Детали сообщения | teacher, head, admin |
| POST | /telegram/send | Заглушка Telegram | teacher, head, admin |
| GET | /events | Список событий | авторизован |
| POST | /events | Создать событие | teacher, head, admin |
| GET | /events/{id} | Детали события | авторизован |
| PUT | /events/{id} | Редактировать | создатель / head / admin |
| DELETE | /events/{id} | Удалить | создатель / head / admin |
| POST | /events/{id}/image | Загрузить фото | создатель / head / admin |
| GET | /documents | Список документов | по visibility |
| POST | /documents | Загрузить документ | teacher, head, admin |
| GET | /documents/{id} | Метаданные | по visibility |
| GET | /documents/{id}/download | Скачать файл | по visibility |
| PUT | /documents/{id} | Обновить метаданные | head, admin |
| DELETE | /documents/{id} | Удалить | admin |
# Архитектура портала кафедры

## Роли пользователей

| Роль | Описание |
|------|----------|
| `student` | Студент — базовый доступ на чтение |
| `headman` | Староста — расширенные права внутри группы |
| `teacher` | Преподаватель — публикация контента, управление посещаемостью |
| `deputy_head` | Заместитель заведующего |
| `dean` | Деканат — управление структурой (потоки, группы, расписание) |
| `admin` | Администратор — полный доступ |

---

## Сущности и их связи

### Структура учебного процесса

```
Stream (поток)
  └── Group (группа)  ←── StudentProfile (профиль студента)
                              └── User
```

- **Stream** — учебный поток (например, ИИТ-22). Создаётся деканатом.
- **Group** — группа внутри потока (например, ИИТ22-01). Создаётся деканатом.
- **StudentProfile** — привязывает пользователя к группе. Содержит телефон, telegram, vk.
- **TeacherProfile** — профиль преподавателя: кафедра, должности (`TeacherPosition`), кабинет.
- **DeanProfile** — профиль деканата: факультет, должность, кабинет.

### Объявления и мероприятия

```
Announcement (объявление)
  ├── target_groups  → Group[]   (кому адресовано)
  ├── target_streams → Stream[]  (кому адресовано)
  ├── Attachment[]               (вложения)
  └── Event (мероприятие) [0..1] (опционально)
            └── room_id → Room
```

- **Announcement** — информационное сообщение с жизненным циклом:
  ```
  draft → scheduled → published → archived → (удаление через 14 дней)
                                  ↑________| восстановление (dean, admin)
  ```

  **Автоматические переходы** — Celery-таска `sync_announcement_statuses` (каждые 60 сек, три шага за один прогон):
  1. `scheduled → published`: если `publish_at <= now`
  2. `published → archived`: если `expires_at <= now` (только при наличии `expires_at`; объявления без него не архивируются автоматически)
  3. `archived → удалено`: если `updated_at <= now - 14 дней` (`updated_at` проставляется явно при автоматической архивации, т.к. bulk `update()` не триггерит ORM `onupdate`)

  **Ручные переходы**:
  - Архивировать: своё — headman/teacher; любое на своей кафедре — deputy_head; любое — dean, admin
  - Восстановить из архива: dean, admin (`PATCH /{id}/restore`)
  - Удалить вручную: автор или admin

  Адресуется конкретным группам (`target_groups`) и/или потокам (`target_streams`).

- **Event** — мероприятие с временем проведения (`starts_at`, `ends_at`) и аудиторией (`room_id → Room`).
  Может быть привязано к объявлению (`announcement_id nullable`) — тогда событие создаётся отдельно и при желании связывается с существующим Announcement.

- **Room** — аудитория: номер, адрес, вместимость.

### Расписание и посещаемость

```
Lesson (занятие)
  ├── group_id  → Group
  ├── teacher_id → User (teacher)
  └── room_id   → Room

AttendanceToken (QR-токен)
  └── lesson_id → Lesson

Attendance (запись о посещении)
  ├── lesson_id  → Lesson
  └── student_id → User
```

- **Lesson** — занятие из расписания (синхронизируется через `/lessons/sync`).
- **AttendanceToken** — одноразовый QR-токен для отметки посещения (живёт 15 минут).
- **Attendance** — факт посещения: студент отмечается сканом QR или вручную преподавателем.

### Чат

```
Chat
  ├── type: group | direct
  ├── group_id → Group  (только для group-чатов)
  ├── ChatMember[] → User[]
  └── ChatMessage[]
        ├── sender_id → User
        └── body
```

- **Chat** — абстракция чата двух видов:
  - `group` — групповой чат, привязан к `Group` (создаётся вместе с группой)
  - `direct` — личная переписка между двумя пользователями (создаётся при первом обращении)
- **ChatMember** — участник чата (many-to-many `Chat ↔ User`)
- **ChatMessage** — сообщение. Сохраняется в БД и в реальном времени рассылается всем подключённым через WebSocket.
- Соединение: `WS /api/v1/chats/{id}/ws?token=...` — авторизация через access token в query-параметре.

### Прочее

- **Document** — файл с полем `visibility` (список ролей, кому виден).
- **Notification** — системное уведомление, привязывается к Announcement или Event.

---

## Флоу авторизации

### Студент
1. `POST /auth/register` — самостоятельная регистрация, роль всегда `student`
2. `POST /auth/login` → `access_token` + `refresh_token`

### Преподаватель / деканат / староста (`teacher`, `dean`, `headman`, `deputy_head`)
Самостоятельная регистрация недоступна — аккаунт создаёт только `admin`:

1. `POST /users` (admin) — передаёт `email`, `name`, `surname`, нужную роль; пароль **не указывается**
2. Бэк генерирует случайный пароль (`generate_password`, 12 символов)
3. Создаёт пользователя в БД
4. Отправляет письмо на указанный email с логином и паролем (`send_credentials_email`)
5. Пользователь логинится через `POST /auth/login` полученными кредами

### Общий механизм токенов
- **Access-токен** (JWT): `sub=user_id`, `role`, `type="access"`. Живёт `ACCESS_TOKEN_EXPIRE_MINUTES`.
- **Refresh-токен** (JWT): `sub`, `jti` (UUID), `type="refresh"`. Хранится в таблице `refresh_tokens` (поле `revoked`). Живёт `REFRESH_TOKEN_EXPIRE_DAYS`.
- `POST /auth/refresh` — rotation: старый refresh отзывается, выдаётся новая пара токенов.
- `POST /auth/logout` — refresh отзывается; access-токен живёт до истечения срока (stateless).
- Защита маршрутов: `require_roles(Role.teacher, ...)` — проверяет `user.role` после декодирования access-токена.

---

## Права доступа по модулям

### Users `/users`
| Действие | Роли |
|----------|------|
| Создать пользователя | admin |
| Список пользователей | headman, admin |
| Просмотр профиля | любой авторизованный |
| Редактировать профиль | сам пользователь, admin |
| Изменить роль | admin |
| Удалить пользователя | admin |

### Streams `/streams`
| Действие | Роли |
|----------|------|
| Список / просмотр | любой авторизованный |
| Создать / изменить / удалить | dean |

### Groups `/groups`
| Действие | Роли |
|----------|------|
| Список / просмотр | любой авторизованный |
| Создать / изменить / удалить | dean |

### Announcements `/announcements`
| Действие | Роли |
|----------|------|
| Список / просмотр | любой авторизованный (фильтрация по группе) |
| Создать | teacher, headman, admin |
| Изменить | своё — headman/teacher; кафедры — deputy_head; любое — dean |
| Архивировать | своё — headman/teacher; кафедры — deputy_head; любое — dean, admin |
| Восстановить из архива | dean, admin |
| Удалить вручную | автор или admin |
| Удалить автоматически | Celery — через 14 дней после архивирования |

### Events `/events`
| Действие | Роли |
|----------|------|
| Список / просмотр | любой авторизованный |
| Создать | teacher, headman, admin |
| Изменить / удалить | автор события, headman, admin |
| Загрузить изображение | автор события, headman, admin |

### Lessons `/lessons`
| Действие | Роли |
|----------|------|
| Расписание группы / преподавателя | любой авторизованный |
| Синхронизировать расписание | dean |

### Attendance `/attendance`
| Действие | Роли |
|----------|------|
| Создать QR-токен | teacher, headman |
| Получить QR-изображение | teacher, headman |
| Отметиться по QR | student, headman |
| Отметить вручную | teacher, headman |
| Просмотр посещаемости занятия / студента | любой авторизованный |

### Chats `/chats`
| Действие | Роли |
|----------|------|
| Список своих чатов | любой авторизованный |
| Открыть личку с пользователем | любой авторизованный |
| История сообщений | участник чата |
| WebSocket (отправка/приём) | участник чата (token в query) |

### Documents `/documents`
| Действие | Роли |
|----------|------|
| Список | любой авторизованный (фильтр по `visibility`) |
| Загрузить | teacher, headman, admin |
| Просмотр / скачать | любой авторизованный, у кого роль в `visibility` |
| Изменить метаданные | headman, admin |
| Удалить | admin |

---

## Известные недоделки

| Место | Проблема |
|-------|----------|
| `users` `PATCH /role`, `DELETE` | эндпоинты объявлены, но тело не реализовано (`pass`) |
| `dependencies.py` | TODO: зависимость для преподавателя → его группы |
