#!/bin/bash
# Одноразовая настройка на сервере
# chmod +x setup.sh && ./setup.sh

set -e

echo "=== Установка системных зависимостей для сборки ==="
if command -v apt-get &>/dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y build-essential python3-dev libpq-dev
elif command -v dnf &>/dev/null; then
    sudo dnf install -y gcc gcc-c++ make python3-devel postgresql-devel
elif command -v yum &>/dev/null; then
    sudo yum install -y gcc gcc-c++ make python3-devel postgresql-devel
else
    echo "Неизвестный пакетный менеджер, установите вручную: gcc, python3-devel, postgresql-devel"
    exit 1
fi
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
if [ -d "./wheels" ]; then
    echo "Найдена папка wheels — установка офлайн"
    venv/bin/pip install --no-index --find-links=./wheels/ -r requirements.txt
else
    echo "Установка из PyPI (нужен интернет)"
    venv/bin/pip install --upgrade pip --timeout 120
    venv/bin/pip install -r requirements.txt --timeout 120
fi

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
