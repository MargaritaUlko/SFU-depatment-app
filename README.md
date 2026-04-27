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

## Роли

| Роль | Значение |
|------|----------|
| `student` | Студент |
| `teacher` | Преподаватель |
| `head` | Заведующий кафедрой |
| `admin` | Администратор системы |

## Тесты

```bash
pytest tests/ -v
```

## Переменные окружения (.env)

```env
DATABASE_URL=postgresql+asyncpg://dept_user:dept_pass@localhost:5432/department_db
SECRET_KEY=<64-символьная-случайная-строка>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
UPLOAD_DIR=uploads
MAX_FILE_SIZE_MB=20
```

## Структура проекта

```
app/
├── core/         # config, security
├── db/           # engine, session, Base
├── models/       # SQLAlchemy ORM модели
├── schemas/      # Pydantic схемы
├── crud/         # Операции с БД
├── services/     # JWT, хранение файлов
├── routers/      # FastAPI роутеры (один файл = один модуль)
├── dependencies.py  # get_current_user, require_roles
└── main.py       # Точка входа FastAPI
alembic/          # Миграции
tests/            # pytest тесты
uploads/          # Загружаемые файлы (gitignored)
```
