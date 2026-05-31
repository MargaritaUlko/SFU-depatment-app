#!/bin/bash
# Запуск API на сервере без Docker
# chmod +x run.sh && ./run.sh

set -e

if [ ! -d "venv" ]; then
    echo "venv не найден. Запустите сначала: ./setup.sh"
    exit 1
fi

echo "=== Применение миграций ==="
venv/bin/alembic upgrade head

echo ""
echo "=== Запуск API ==="
echo "Swagger: http://localhost:8000/docs"
venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
