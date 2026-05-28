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

## Сущности и их связи

### Диаграмма связей

```
Stream (поток)
  └── Group (группа) ──────────────── Lesson (занятие) ──── User (teacher)
        │                                    │
        │                               Attendance ──── User (student)
        │                            AttendanceToken
        └── StudentProfile ─── User
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
             TeacherProfile  DeanProfile  RefreshToken
                    │
              Chat (group) ── ChatMember ── User
                    │
              ChatMessage ── User (sender)

User (direct) ── Chat (direct) ── ChatMember ── User

User ── Document
User ── Announcement ──┬── announcement_groups ── Group
                       ├── announcement_streams ── Stream
                       ├── Attachment
                       ├── Event ── Room
                       │       └── Notification ── NotificationReceipt ── User
                       └── Notification ── NotificationReceipt ── User

User ── VKRTopic (proposed_by)
User ── VKRTopic (student)
```

---

## Описание сущностей

### User — Пользователь

Таблица: `users`

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | |
| name | String(100) | Имя |
| surname | String(100) | Фамилия |
| patronymic | String(100) nullable | Отчество |
| email | String(255) unique | Email, используется для входа |
| hashed_password | String(255) | Bcrypt-хэш |
| role | Enum(Role) | Роль (см. ниже) |
| is_active | Boolean | Активен ли аккаунт |
| avatar | String(500) nullable | Путь к файлу аватарки |

**Роли:**
- `student` — студент, регистрируется сам
- `headman` — староста, создаётся админом
- `teacher` — преподаватель, создаётся админом
- `deputy_head` — зав. кафедрой, создаётся админом
- `dean` — деканат, создаётся админом
- `admin` — администратор

**Связи:**
- → `StudentProfile` (1:1, nullable — только для student/headman)
- → `TeacherProfile` (1:1, nullable — только для teacher/deputy_head)
- → `DeanProfile` (1:1, nullable — только для dean)
- → `RefreshToken` (1:N)
- → `Document` (1:N, как загрузчик)
- → `Announcement` (1:N, как автор)
- → `Event` (1:N, как создатель)
- → `ChatMember` (M:N через chat_members)
- → `ChatMessage` (1:N, как отправитель)
- → `VKRTopic` (1:N, как предложивший и/или как студент)
- → `Attendance` (1:N, как студент)
- → `NotificationReceipt` (1:N)

---

### StudentProfile — Профиль студента

Таблица: `student_profiles`

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | |
| user_id | FK → users (unique) | Пользователь |
| group_id | FK → groups | Группа студента |
| phone | String(20) nullable | |
| telegram | String(100) nullable | |
| vk | String(100) nullable | |

Создаётся автоматически при регистрации студента или при создании старосты через `/users`.

---

### TeacherProfile — Профиль преподавателя / зав. кафедрой

Таблица: `teacher_profiles`

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | |
| user_id | FK → users (unique) | Пользователь |
| department | String(255) nullable | Кафедра |
| positions | ARRAY(TeacherPosition) nullable | Должности (массив) |
| phone | String(20) nullable | |
| cabinet | String(50) nullable | |

**TeacherPosition:** assistant, lecturer, senior_lecturer, associate_professor, professor, sfu_professor, acting_head

Используется и для роли `teacher`, и для `deputy_head`.

---

### DeanProfile — Профиль деканата

Таблица: `dean_profiles`

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | |
| user_id | FK → users (unique) | Пользователь |
| faculty | String(255) NOT NULL default="" | Факультет |
| position | String(255) nullable | Должность |
| phone | String(20) nullable | |
| cabinet | String(50) nullable | |

---

### Stream — Поток

Таблица: `streams`

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | |
| name | String(100) | Название потока |
| year | Integer | Год набора |
| speciality | String(255) | Специальность |

**Связи:**
- → `Group` (1:N) — группы внутри потока
- ← `Announcement` (M:N через announcement_streams) — объявления для потока

---

### Group — Группа

Таблица: `groups`

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | |
| name | String(100) | Название группы |
| stream_id | FK → streams nullable | Поток (SET NULL при удалении) |
| year | Integer | Год набора |

**Связи:**
- → `StudentProfile` (1:N) — студенты группы
- → `Lesson` (1:N) — занятия группы
- → `Chat` (1:1, nullable) — групповой чат
- ← `Announcement` (M:N через announcement_groups) — объявления для группы

---

### Lesson — Занятие (расписание)

Таблица: `lessons`

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | |
| group_id | FK → groups (CASCADE) | Группа |
| teacher_id | FK → users nullable (SET NULL) | Преподаватель |
| teacher_name | String(255) nullable | Имя преподавателя (денормализовано) |
| day | Integer | День недели (1–7) |
| week | Integer | Тип недели (1=нечёт, 2=чёт) |
| time_start | String(10) | Время начала |
| time_end | String(10) | Время окончания |
| subject | String(500) | Название предмета |
| lesson_type | String(100) nullable | Тип занятия |
| room | String(200) nullable | Аудитория |
| building | String(200) nullable | Корпус |

Уникальный индекс: `(group_id, day, week, time_start, subject)`.

**Связи:**
- → `Attendance` (1:N) — отметки присутствия
- → `AttendanceToken` (1:N) — QR-токены для отметки

---

### Attendance — Посещаемость

Таблица: `attendance`

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | |
| lesson_id | FK → lessons (CASCADE) | Занятие |
| student_id | FK → users (CASCADE) | Студент |
| marked_via | String(10) | Способ отметки: `qr` или `manual` |

Уникальный индекс: `(lesson_id, student_id)` — студент может быть отмечен на занятии только один раз.

---

### AttendanceToken — QR-токен посещаемости

Таблица: `attendance_tokens`

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | |
| lesson_id | FK → lessons (CASCADE) | Занятие |
| token | String unique | UUID-токен |
| expires_at | DateTime | Время истечения |
| is_active | Boolean | Активен ли токен |

Преподаватель генерирует токен для занятия, студент сканирует QR — отметка фиксируется в `attendance`.

---

### Chat — Чат

Таблица: `chats`

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | |
| type | Enum(ChatType) | `direct` или `group` |
| group_id | FK → groups nullable (CASCADE, unique) | Только для group-чата |

**Связи:**
- → `ChatMember` (1:N, cascade delete) — участники
- → `ChatMessage` (1:N, cascade delete) — сообщения
- ← `Group` (1:1, nullable) — для group-чата

Групповой чат создаётся по академической группе (group_id unique — у одной группы один чат). Личный чат (direct) не привязан к группе.

---

### ChatMember — Участник чата

Таблица: `chat_members`

| Поле | Тип | Описание |
|------|-----|----------|
| chat_id | FK → chats PK (CASCADE) | |
| user_id | FK → users PK (CASCADE) | |

Составной PK. Уникальный индекс: `(chat_id, user_id)`.

---

### ChatMessage — Сообщение

Таблица: `chat_messages`

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | |
| chat_id | FK → chats (CASCADE) | Чат |
| sender_id | FK → users (CASCADE) | Отправитель |
| body | Text | Текст сообщения |

---

### Announcement — Объявление

Таблица: `announcements`

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | |
| title | String(500) | Заголовок |
| content | Text | Содержимое |
| author_id | FK → users | Автор |
| status | Enum(AnnouncementStatus) | draft / scheduled / published / archived |
| publish_at | DateTime nullable | Запланированная публикация |
| expires_at | DateTime nullable | Время архивации |

**Связи:**
- → `Attachment` (1:N, cascade) — вложения
- ↔ `Group` (M:N через announcement_groups) — целевые группы
- ↔ `Stream` (M:N через announcement_streams) — целевые потоки
- → `Event` (1:1, nullable) — связанное мероприятие
- → `Notification` (1:N, cascade) — уведомления

Если `target_groups` и `target_streams` пустые — объявление видят все.

---

### Attachment — Вложение к объявлению

Таблица: `attachments`

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | |
| announcement_id | FK → announcements | |
| filename | String(255) | Имя файла на диске |
| original_name | String(255) | Оригинальное имя |
| content_type | String(100) | MIME-тип |
| size_bytes | Integer | Размер |

---

### Event — Мероприятие

Таблица: `events`

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | |
| announcement_id | FK → announcements nullable (SET NULL, unique) | Объявление-источник |
| title | String(255) | Название |
| annotation | Text nullable | Описание |
| starts_at | DateTime | Начало |
| ends_at | DateTime | Конец |
| room_id | FK → rooms nullable (SET NULL) | Аудитория |
| image_url | String(500) nullable | Изображение |
| creator_id | FK → users (CASCADE) | Создатель |

**Связи:**
- → `Room` — место проведения
- ← `Announcement` (1:1, nullable) — может быть создано из объявления
- → `Notification` (1:N, cascade)

---

### Room — Аудитория

Таблица: `rooms`

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | |
| number | String(100) | Номер аудитории |
| address | String(500) | Адрес / корпус |
| capacity | Integer nullable | Вместимость |

**Связи:**
- → `Event` (1:N)

---

### Document — Документ

Таблица: `documents`

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | |
| title | String(255) | Название |
| description | Text nullable | Описание |
| category | String(100) | Категория |
| visibility | JSON | Список ролей, которым виден документ |
| file_path | String(500) | Путь к файлу |
| file_name | String(255) | Имя файла |
| uploader_id | FK → users (CASCADE) | Загрузчик |

`visibility` — JSON-массив строк с именами ролей, например `["student", "teacher"]`. Пустой массив = видно всем.

---

### Notification — Уведомление

Таблица: `notifications`

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | |
| scheduled_at | DateTime | Когда отправить |
| event_id | FK → events nullable | Источник: мероприятие |
| announcement_id | FK → announcements nullable | Источник: объявление |
| type | Enum(NotificationType) nullable | `announce` или `reminder` (только для event) |

**Ограничения:**
- Ровно одно из `event_id` / `announcement_id` заполнено (CHECK constraint)
- `type` заполнен только если `event_id` не NULL (CHECK constraint)
- Уникальный индекс: `(event_id, type)` — у одного мероприятия не может быть двух уведомлений одного типа

**Связи:**
- → `NotificationReceipt` (1:N, cascade) — факт доставки каждому пользователю

---

### NotificationReceipt — Квитанция уведомления

Таблица: `notification_receipts`

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | |
| notification_id | FK → notifications (CASCADE) | |
| user_id | FK → users (CASCADE) | Получатель |
| is_read | Boolean | Прочитано |
| read_at | DateTime nullable | Когда прочитано |

Уникальный индекс: `(notification_id, user_id)`.

---

### VKRTopic — Тема ВКР

Таблица: `vkr_topics`

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | |
| title | String(500) | Название темы |
| description | Text nullable | Описание |
| proposed_by_id | FK → users (CASCADE) | Кто предложил (student/headman/teacher) |
| student_id | FK → users nullable (SET NULL) | Закреплённый студент |
| status | Enum(VKRStatus) | pending / approved / rejected |
| head_comment | Text nullable | Комментарий зав. кафедрой |

Тема предлагается студентом или преподавателем. При предложении от студента `student_id` = `proposed_by_id`. Одобряет/отклоняет зав. кафедрой (`deputy_head`). При отклонении `head_comment` обязателен.

---

### RefreshToken — Refresh-токен

Таблица: `refresh_tokens`

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer PK | |
| jti | String unique | JWT ID токена |
| user_id | FK → users (CASCADE) | Пользователь |
| revoked | Boolean | Отозван |
| expires_at | DateTime | Истечение |

---

## Аутентификация

- `POST /api/v1/auth/register` — самостоятельная регистрация студента
- `POST /api/v1/auth/login` — вход (OAuth2 form), возвращает access + refresh токены
- `POST /api/v1/auth/refresh` — обновление токенов (старый отзывается, выдаётся новая пара)
- `POST /api/v1/auth/logout` — отзыв refresh-токена
- `POST /api/v1/auth/reset-password` — сброс пароля, новый отправляется на email
- `GET /api/v1/auth/me` — текущий пользователь

**Bearer-схема:** `HTTPBearer`. Токен в заголовке `Authorization: Bearer <token>`.

---

## Пользователи — эндпоинты

### Создание

**Студент** регистрируется сам через `POST /auth/register` (схема `StudentRegister`):
```json
{ "name", "surname", "patronymic"?, "email", "password", "group_id" }
```

**Все остальные роли** создаются администратором через `POST /users` (схема `UserCreate`):
```json
{ "name", "surname", "patronymic"?, "email", "role", "group_id"? }
```
Пароль для headman, teacher, deputy_head, dean генерируется автоматически и отправляется на email. При создании автоматически создаётся профиль соответствующего типа.

### Обновление профиля

- `PATCH /users/me/student-profile` — только student, headman → поля: group_id, phone, telegram, vk
- `PATCH /users/me/teacher-profile` — только teacher, deputy_head → поля: department, positions, phone, cabinet
- `PATCH /users/me/dean-profile` — только dean → поля: faculty, position, phone, cabinet

### Остальные

- `GET /users` — список пользователей (видимость зависит от роли, см. ниже)
- `GET /users/teachers` — преподаватели и зав. кафедрой **без телефона** (для авторизованных)
- `GET /users/search?surname=` — поиск по фамилии
- `PUT /users/{id}` — обновление ФИО и email
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

## Чат — эндпоинты

- `GET /chats` — список чатов (admin видит все, остальные — свои)
- `POST /chats/group` — создать групповой чат
- `GET /chats/direct/{user_id}` — получить или создать личный чат
- `GET /chats/{id}/messages` — история сообщений (admin может читать любой чат)
- `POST /chats/{id}/messages` — отправить сообщение через REST
- `WS /chats/{id}/ws` — WebSocket (токен передаётся query-параметром)

---

## ВКР — эндпоинты

- `POST /vkr/topics` — предложить тему (student, headman, teacher)
- `GET /vkr/my-topics` — мои темы
- `GET /vkr/topics` — все темы с фильтром `?status=` (deputy_head, admin)
- `GET /vkr/topics/approved` — одобренные (dean, deputy_head, admin)
- `GET /vkr/topics/{id}` — детали (автор видит свою, привилегированные — любую)
- `POST /vkr/topics/{id}/review` — одобрить/отклонить (deputy_head)

---

## Объявления — эндпоинты

- `GET /announcements` — список с фильтрацией по роли пользователя
- `GET /announcements/my` — объявления текущего пользователя
- `POST /announcements` — создать
- `PUT /announcements/{id}` — обновить
- `DELETE /announcements/{id}` — soft delete (→ archived)
- `POST /announcements/{id}/restore` — восстановить

---

## Email

`app/core/email.py`. Внутренний хелпер `_send_email(to, subject, body)`.

- `send_credentials_email` — при создании пользователя через admin
- `send_password_reset_email` — при сбросе пароля

Требует `RESEND_API_KEY` в `.env`. При отсутствии — логирует предупреждение, письмо не отправляется.

---

## Административная панель

URL: `http://localhost:8000/admin`  
Вход: email + пароль пользователя с ролью `admin`

| View | Модель | Права |
|------|--------|-------|
| UserAdmin | User | просмотр, редактирование |
| RefreshTokenAdmin | RefreshToken | просмотр, удаление |
| StreamAdmin | Stream | CRUD |
| GroupAdmin | Group | CRUD |
| ChatAdmin | Chat | просмотр, удаление |
| ChatMessageAdmin | ChatMessage | просмотр, экспорт |
| EventAdmin | Event | CRUD |
| DocumentAdmin | Document | CRUD |

---

## CI/CD

`.gitlab-ci.yml` — три стадии: **build → test → deploy**.

- **build**: собирает Docker-образ, пушит в GitLab Registry
- **test**: запускает `pytest` внутри образа
- **deploy**: только из ветки `main`, подключается по SSH, перезапускает контейнер

---

## Миграции

```bash
docker compose exec api alembic upgrade head
```

Цепочка:
```
49db932424b1  — начальные таблицы
    ↓
b3c4d5e6f7a8  — замена messages на chat
    ↓
aa3f86f1e167  — announcement_id nullable в events
    ↓
f1a2b3c4d5e6  — роль deputy_head
    ↓
019304363317  — таблица vkr_topics
```
