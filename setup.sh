#!/bin/bash
# Одноразовая настройка на сервере
# chmod +x setup.sh && ./setup.sh

set -e

echo "=== Установка системных зависимостей для сборки ==="
if command -v apt-get &>/dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y build-essential python3-dev
else
    command -v gcc &>/dev/null || { echo "ОШИБКА: gcc не найден. Установите вручную."; exit 1; }
fi
echo "Готово."

echo ""
echo "=== Создание виртуального окружения ==="
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "venv создан."
else
    echo "venv уже существует."
fi

echo ""
echo "=== Установка Python-зависимостей ==="
if [ -d "./wheels" ]; then
    echo "Найдена папка wheels — офлайн-установка"
    venv/bin/pip install --no-index --find-links=./wheels/ -r requirements.txt
else
    echo "Установка из PyPI..."
    venv/bin/pip install --upgrade pip --timeout 120 --quiet
    venv/bin/pip install -r requirements.txt --timeout 120 || {
        echo ""
        echo "ОШИБКА: pip не может скачать пакеты (нет интернета?)."
        echo ""
        echo "Решение — скачайте пакеты на Windows-машине и перенесите:"
        echo "  1. На Windows:"
        echo "       pip download -r requirements.txt -d ./wheels/ \\"
        echo "           --platform manylinux2014_x86_64 --python-version 3.12 \\"
        echo "           --implementation cp --only-binary=:all:"
        echo "       scp -r wheels/ mulko@<IP>:/home/mulko/SFU-depatment-app/"
        echo "  2. Запустите снова: ./setup.sh"
        exit 1
    }
fi

echo ""
echo "=== Создание папок для файлов ==="
mkdir -p uploads/events uploads/documents uploads/avatars
echo "Готово."

echo ""
echo "Установка завершена! Следующие шаги:"
echo "  1. Убедитесь, что PostgreSQL и Redis запущены"
echo "  2. Создайте БД (если ещё не создана):"
echo "       sudo -u postgres psql -c \"CREATE USER dept_user WITH PASSWORD 'dept_pass';\""
echo "       sudo -u postgres psql -c \"CREATE DATABASE department_db OWNER dept_user;\""
echo "  3. Скопируйте и заполните .env: cp .env.example .env"
echo "  4. Запустите: ./run.sh"
