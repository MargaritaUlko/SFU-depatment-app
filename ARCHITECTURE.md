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

#### Подключение к чату (для фронта)

**1. Получить чат**
- Личка: `POST /api/v1/chats/direct/{user_id}` — возвращает `{id, type, members, ...}`
- Групповой: `POST /api/v1/chats/group` — `{"group_id": 1, "member_ids": [1, 2, 3]}`
- Список своих чатов: `GET /api/v1/chats`

**2. Подключиться по WebSocket**
```
ws://HOST/api/v1/chats/{chat_id}/ws?token=<access_token>
```
- `access_token` — тот же JWT, что используется в заголовке `Authorization: Bearer ...`
- Передаётся **в query-параметре** `token`, а не в заголовке (WebSocket API браузера не позволяет задавать кастомные заголовки)

**3. Отправить сообщение**

Отправить plain text-строку (не JSON):
```
Привет!
```

**4. Входящие сообщения**

Все участники чата получают JSON:
```json
{
  "id": 42,
  "chat_id": 9,
  "sender_id": 3,
  "body": "Привет!",
  "created_at": "2026-05-16T12:35:00.123456"
}
```

**Коды закрытия соединения:**
| Код | Причина |
|-----|---------|
| `4001` | Невалидный или просроченный токен |
| `4003` | Пользователь не является участником чата |

**Пример на JS:**
```js
const ws = new WebSocket(
  `ws://localhost:8000/api/v1/chats/${chatId}/ws?token=${accessToken}`
);
ws.onmessage = (e) => console.log(JSON.parse(e.data));
ws.onopen = () => ws.send("Привет!");
ws.onclose = (e) => console.log("Closed:", e.code);
```

### Прочее

- **Document** — файл с полем `visibility`. Поддерживает гранулярную видимость:
  - `role:student` / `role:teacher` / ... — по роли
  - `group:5` — конкретная группа
  - `stream:2` — конкретный поток
  - Простые строки без префикса (legacy): `student`, `teacher` и т.д.
- **Notification** — системное уведомление, привязывается к Announcement или Event.

---

## Флоу авторизации

### Студент
1. `POST /auth/register` — самостоятельная регистрация, роль всегда `student`
2. `POST /auth/login` → `access_token` + `refresh_token`

### Преподаватель / деканат / староста (`teacher`, `dean`, `headman`, `deputy_head`)
Самостоятельная регистрация недоступна — аккаунт создаёт только `admin`:

1. `POST /users` (admin) — передаёт `email`, `name`, `surname`, `patronymic` (опц.), нужную роль; поле `password` игнорируется
2. Бэк генерирует случайный пароль (`generate_password`, 12 символов)
3. Создаёт пользователя в БД
4. Отправляет письмо на указанный email с логином и паролем (`send_credentials_email`); ошибка отправки не прерывает создание — только логируется
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
| Действие | Метод | Роли |
|----------|-------|------|
| Создать пользователя | `POST /users` | admin |
| Список пользователей | `GET /users` | headman, admin |
| Просмотр профиля | `GET /users/{id}` | любой авторизованный |
| Редактировать профиль | `PUT /users/{id}` | сам пользователь, admin |
| Сменить пароль | `PATCH /users/{id}/password` | сам пользователь, admin |
| Загрузить аватар | `PATCH /users/me/avatar` | любой авторизованный |
| Получить аватар | `GET /users/{id}/avatar` | любой авторизованный |
| Удалить пользователя | `DELETE /users/{id}` | admin |

`UserRead` содержит: `id`, `name`, `surname`, `patronymic`, `email`, `role`, `is_active`, `avatar`, `created_at`, `updated_at`.

`UserUpdate` позволяет изменить только: `name`, `surname`, `patronymic`, `email` (роль и пароль — отдельными эндпоинтами).

Аватары сохраняются в `UPLOAD_DIR/avatars/`. При загрузке нового аватара старый файл удаляется с диска. Допустимые форматы: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp`.

Логика создания (`POST /users`):
- Роли `headman`, `teacher`, `dean`, `deputy_head` — пароль генерируется автоматически и отправляется на email (`send_credentials_email`). Поле `password` в запросе игнорируется.
- Роли `student`, `admin` — пароль передаётся явно в теле запроса.

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
| Действие | Метод | Роли |
|----------|-------|------|
| Список | `GET /documents` | любой авторизованный (фильтр по `visibility`) |
| Загрузить | `POST /documents` | teacher, deputy_head, admin |
| Просмотр метаданных | `GET /documents/{id}` | любой авторизованный, у кого доступ по `visibility` |
| Скачать файл | `GET /documents/{id}/download` | любой авторизованный, у кого доступ по `visibility` |
| Изменить метаданные | `PUT /documents/{id}` | headman, admin |
| Удалить | `DELETE /documents/{id}` | admin |

`visibility` принимается как строка через `Form` (multipart): можно JSON-массив `["role:student","group:5"]` или список через запятую `role:student, group:5`. Валидируется на сервере — несуществующие группы/потоки возвращают 400.

`DocumentRead` содержит: `id`, `title`, `description`, `category`, `visibility`, `file_name`, `uploader_id`, `created_at`, `updated_at`.

---

## Известные недоделки

| Место | Проблема |
|-------|----------|
| `users/crud.py` `update_user_password` | устанавливает `user.password` вместо `user.hashed_password` — пароль не хешируется |
| `users/router.py` | нет эндпоинта `PATCH /{id}/role` для смены роли (функция `update_user_role` в crud есть, роутер не подключён) |
| `dependencies.py` | TODO: зависимость для преподавателя → его группы |
