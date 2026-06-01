# Матрица прав доступа

**Роли:** `student` | `headman` (ст-та) | `teacher` | `deputy_head` (зам. зав.) | `dean` (деканат) | `admin`

**Обозначения:**
- `✓` — полный доступ
- `R` — только чтение
- `○` — только свои записи
- `R*` — чтение с фильтрацией по видимости
- `—` — нет доступа

---

## AUTH `/auth`

| Действие               | student | headman | teacher | deputy_head | dean | admin |
|------------------------|:-------:|:-------:|:-------:|:-----------:|:----:|:-----:|
| POST /register         | ✓       | ✓       | ✓       | ✓           | ✓    | ✓     |
| POST /login            | ✓       | ✓       | ✓       | ✓           | ✓    | ✓     |
| POST /refresh          | ✓       | ✓       | ✓       | ✓           | ✓    | ✓     |
| POST /logout           | ✓       | ✓       | ✓       | ✓           | ✓    | ✓     |
| POST /reset-password   | ✓       | ✓       | ✓       | ✓           | ✓    | ✓     |

> Все эндпоинты публичные (не требуют токена).

---

## USERS `/users`

| Действие                       | student | headman | teacher | deputy_head | dean | admin |
|--------------------------------|:-------:|:-------:|:-------:|:-----------:|:----:|:-----:|
| POST / (создать пользователя)  | —       | —       | —       | —           | —    | ✓     |
| GET /me                        | ✓       | ✓       | ✓       | ✓           | ✓    | ✓     |
| GET /teachers                  | R       | R       | R       | R           | R    | R     |
| GET / (список пользователей)   | R*      | R*      | R*      | R*          | R*   | R     |
| GET /search                    | R       | R       | R       | R           | R    | R     |
| PUT /{id} (обновить профиль)   | ○       | ○       | ○       | ○           | ○    | ✓     |
| PATCH /{id}/password           | ○       | ○       | ○       | ○           | ○    | ✓     |
| PATCH /me/avatar               | ✓       | ✓       | ✓       | ✓           | ✓    | ✓     |
| GET /{id}/avatar               | R       | R       | R       | R           | R    | R     |
| PATCH /me/student-profile      | ✓       | ✓       | —       | —           | —    | —     |
| PATCH /me/teacher-profile      | —       | —       | ✓       | ✓           | —    | —     |
| PATCH /me/dean-profile         | —       | —       | —       | —           | ✓    | —     |
| PATCH /{id}/group              | —       | —       | —       | —           | ✓    | —     |
| DELETE /{id}                   | —       | —       | —       | —           | —    | ✓     |

---

## GROUPS `/groups`

| Действие           | student | headman | teacher | deputy_head | dean | admin |
|--------------------|:-------:|:-------:|:-------:|:-----------:|:----:|:-----:|
| GET / (список)     | R       | R       | R       | R           | R    | R     |
| POST /             | —       | —       | —       | —           | ✓    | ✓     |
| GET /{id}          | R       | R       | R       | R           | R    | R     |
| PATCH /{id}        | —       | —       | —       | —           | ✓    | ✓     |
| DELETE /{id}       | —       | —       | —       | —           | ✓    | ✓     |

---

## STREAMS `/streams`

| Действие           | student | headman | teacher | deputy_head | dean | admin |
|--------------------|:-------:|:-------:|:-------:|:-----------:|:----:|:-----:|
| GET / (список)     | R       | R       | R       | R           | R    | R     |
| POST /             | —       | —       | —       | —           | ✓    | ✓     |
| GET /{id}          | R       | R       | R       | R           | R    | R     |
| PATCH /{id}        | —       | —       | —       | —           | ✓    | ✓     |
| DELETE /{id}       | —       | —       | —       | —           | ✓    | ✓     |

---

## DOCUMENTS `/documents`

| Действие              | student | headman | teacher | deputy_head | dean | admin |
|-----------------------|:-------:|:-------:|:-------:|:-----------:|:----:|:-----:|
| GET / (список)        | R*      | R*      | R*      | R*          | R*   | R     |
| POST / (загрузить)    | —       | —       | ✓       | ✓           | ✓    | ✓     |
| GET /{id}             | R*      | R*      | R*      | R*          | R*   | R     |
| GET /{id}/download    | R*      | R*      | R*      | R*          | R*   | R     |
| PUT /{id} (обновить)  | —       | —       | ○       | ○           | ○    | ✓     |
| DELETE /{id}          | —       | —       | ○       | ○           | ○    | ✓     |

> `R*` — видят только документы, где их роль/группа/поток указаны в `visibility`.

---

## ANNOUNCEMENTS `/announcements`

| Действие                  | student | headman | teacher | deputy_head | dean | admin |
|---------------------------|:-------:|:-------:|:-------:|:-----------:|:----:|:-----:|
| GET / (список)            | R       | R       | R       | R           | R    | R     |
| GET /my                   | R       | R       | R       | R           | R    | R     |
| POST /                    | —       | ✓       | ✓       | ✓           | ✓    | ✓     |
| GET /{id}                 | R       | R       | R       | R           | R    | R     |
| PATCH /{id} (обновить)    | —       | ✓       | ✓       | ✓           | ✓    | ✓     |
| PATCH /{id}/archive       | —       | ✓       | —       | ✓           | ✓    | ✓     |
| PATCH /{id}/restore       | —       | —       | —       | —           | ✓    | ✓     |
| DELETE /{id}              | ○       | ○       | ○       | ○           | ○    | ✓     |

---

## EVENTS `/events`

| Действие                   | student | headman | teacher | deputy_head | dean | admin |
|----------------------------|:-------:|:-------:|:-------:|:-----------:|:----:|:-----:|
| GET / (список)             | R       | R       | R       | R           | R    | R     |
| POST /                     | —       | ✓       | ✓       | ✓           | ✓    | ✓     |
| GET /{id}                  | R       | R       | R       | R           | R    | R     |
| GET /{id}/image            | R       | R       | R       | R           | R    | R     |
| PUT /{id} (обновить)       | —       | ○       | ○       | ✓           | ✓    | ✓     |
| DELETE /{id}               | —       | ○       | ○       | ✓           | ✓    | ✓     |
| POST /{id}/image (загрузить) | —     | ○       | ○       | ✓           | ✓    | ✓     |

> `○` для teacher/headman — только своё событие (creator_id == current_user.id).

---

## LESSONS `/lessons`

| Действие                     | student | headman | teacher | deputy_head | dean | admin |
|------------------------------|:-------:|:-------:|:-------:|:-----------:|:----:|:-----:|
| GET /group/{id}              | R       | R       | R       | R           | R    | R     |
| GET /teacher/{id}            | R       | R       | R       | R           | R    | R     |
| POST /sync (синхронизация)   | —       | —       | —       | —           | ✓    | ✓     |

---

## ATTENDANCE `/attendance`

| Действие                              | student | headman | teacher | deputy_head | dean | admin |
|---------------------------------------|:-------:|:-------:|:-------:|:-----------:|:----:|:-----:|
| POST /token/{lesson_id} (QR-токен)    | —       | ✓       | ✓       | ✓           | —    | —     |
| GET /token/{lesson_id}/qr             | —       | ✓       | ✓       | ✓           | —    | —     |
| POST /scan/{token} (отметиться по QR) | ✓       | ✓       | —       | —           | —    | —     |
| POST /manual/{lesson}/{student}       | —       | ✓       | ✓       | ✓           | —    | —     |
| GET /lesson/{lesson_id}               | R       | R       | R       | R           | R    | R     |
| GET /student/{student_id}             | R       | R       | R       | R           | R    | R     |

---

## MESSAGES `/messages`

| Действие               | student | headman | teacher | deputy_head | dean | admin |
|------------------------|:-------:|:-------:|:-------:|:-----------:|:----:|:-----:|
| POST / (отправить)     | —       | ✓       | ✓       | ✓           | —    | ✓     |
| GET / (список)         | —       | R       | R       | R           | —    | R     |
| GET /{id}              | —       | ○       | ○       | ○           | —    | ✓     |
| PUT /{id}              | —       | —       | —       | —           | —    | —     |
| DELETE /{id}           | —       | —       | —       | —           | —    | —     |

> PUT/DELETE не реализованы (заглушки).

---

## CHAT `/chats`

| Действие                        | student | headman | teacher | deputy_head | dean | admin |
|---------------------------------|:-------:|:-------:|:-------:|:-----------:|:----:|:-----:|
| GET / (мои чаты)                | R       | R       | R       | R           | R    | R*    |
| POST /direct/{user_id}          | ✓       | ✓       | ✓       | ✓           | ✓    | ✓     |
| POST /group                     | ✓       | ✓       | ✓       | ✓           | ✓    | ✓     |
| POST /{id}/messages             | ✓       | ✓       | ✓       | ✓           | ✓    | ✓     |
| GET /{id}/messages              | R       | R       | R       | R           | R    | R     |
| WS /{id}/ws (real-time)         | ✓       | ✓       | ✓       | ✓           | ✓    | ✓     |

> `R*` для admin — видит все чаты системы. Запись в чат/чтение сообщений — только для участников (admin является исключением при проверке membership).

---

## VKR `/vkr`

| Действие                              | student | headman | teacher | deputy_head | dean | admin |
|---------------------------------------|:-------:|:-------:|:-------:|:-----------:|:----:|:-----:|
| POST /topics (предложить тему)        | ✓       | ✓       | ✓       | ✓           | —    | —     |
| GET /my-topics                        | R       | R       | R       | R           | R    | R     |
| GET /topics/approved                  | —       | —       | —       | ✓           | ✓    | ✓     |
| GET /topics (все темы)                | —       | —       | —       | ✓           | —    | ✓     |
| GET /topics/{id}                      | R       | R       | R       | R           | R    | R     |
| DELETE /topics (массовое удаление)    | —       | —       | —       | ✓           | —    | ✓     |
| POST /topics/{id}/review (рецензия)   | —       | —       | —       | ✓           | —    | —     |

---

## Сводная таблица по модулям

| Модуль        | student       | headman        | teacher        | deputy_head    | dean           | admin |
|---------------|:-------------:|:--------------:|:--------------:|:--------------:|:--------------:|:-----:|
| Auth          | все           | все            | все            | все            | все            | все   |
| Users         | R + свой      | R + свой       | R + свой       | R + свой       | R + управление | CRUD  |
| Groups        | R             | R              | R              | R              | CRUD           | CRUD  |
| Streams       | R             | R              | R              | R              | CRUD           | CRUD  |
| Documents     | R (видимость) | R (видимость)  | CRU свои       | CRU свои       | CRU свои       | CRUD  |
| Announcements | R             | CRD + archive  | CRD            | CRD + archive  | CRUD + restore | CRUD  |
| Events        | R             | CRD свои       | CRD свои       | CRUD           | CRUD           | CRUD  |
| Lessons       | R             | R              | R              | R              | R + sync       | R + sync |
| Attendance    | scan QR       | QR + ручная    | QR + ручная    | QR + ручная    | R              | R     |
| Messages      | —             | CRD свои       | CRD свои       | CRD свои       | —              | CRUD  |
| Chat          | ✓             | ✓              | ✓              | ✓              | ✓              | ✓ (все чаты) |
| VKR           | предложить    | предложить     | предложить     | рецензия + все | approved       | CRUD  |
