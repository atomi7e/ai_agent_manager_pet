# 1. Используем легкую версию Python
FROM python:3.11-slim

# 2. Устанавливаем рабочую папку внутри контейнера
WORKDIR /app

# 3. Сначала копируем зависимости (чтобы кэшировать их)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Копируем весь твой код
COPY . .

# 5. ВАЖНО: Говорим питону, что /app - это главная папка
# Это решит проблему "ModuleNotFoundError: No module named src"
ENV PYTHONPATH=/app

# (Порт и команда запуска будут в docker-compose)