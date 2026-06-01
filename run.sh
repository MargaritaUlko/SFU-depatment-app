#!/bin/bash
# Запуск API на сервере
# chmod +x run.sh && ./run.sh

set -e

if [ ! -f "venv/bin/uvicorn" ]; then
    echo "ОШИБКА: зависимости не установлены. Запустите: ./setup.sh"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "ОШИБКА: файл .env не найден. Скопируйте: cp .env.example .env"
    exit 1
fi

echo "=== Применение миграций ==="
venv/bin/alembic upgrade head

echo ""
echo "=== Запуск API ==="
echo "Swagger: http://localhost:8000/docs"
venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
