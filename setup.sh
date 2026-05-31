#!/bin/bash
# Одноразовая настройка на сервере
# chmod +x setup.sh && ./setup.sh

set -e

echo "=== Установка системных зависимостей для сборки ==="
sudo apt-get update -qq
sudo apt-get install -y build-essential python3-dev libpq-dev
echo "Системные зависимости установлены."

echo ""
echo "=== Создание виртуального окружения ==="
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "venv создан."
else
    echo "venv уже существует."
fi

echo ""
echo "=== Установка зависимостей ==="
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

echo ""
echo "=== Создание папок для файлов ==="
mkdir -p uploads/events uploads/documents uploads/avatars
echo "Папки uploads созданы."

echo ""
echo "Готово! Следующие шаги:"
echo "  1. Убедитесь, что PostgreSQL и Redis запущены"
echo "  2. Создайте БД (если ещё не создана):"
echo "       sudo -u postgres psql -c \"CREATE USER dept_user WITH PASSWORD 'dept_pass';\""
echo "       sudo -u postgres psql -c \"CREATE DATABASE department_db OWNER dept_user;\""
echo "  3. Запустите: ./run.sh"
