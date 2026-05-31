#!/bin/bash
# Запуск Celery worker + beat (требует Redis)
# chmod +x run_workers.sh && ./run_workers.sh

if [ ! -d "venv" ]; then
    echo "venv не найден. Запустите сначала: ./setup.sh"
    exit 1
fi

echo "Запуск Celery worker..."
venv/bin/celery -A app.celery_app worker --loglevel=info &
WORKER_PID=$!

echo "Запуск Celery beat..."
venv/bin/celery -A app.celery_app beat --loglevel=info &
BEAT_PID=$!

echo "Worker PID: $WORKER_PID, Beat PID: $BEAT_PID"
echo "Для остановки: kill $WORKER_PID $BEAT_PID"

wait
