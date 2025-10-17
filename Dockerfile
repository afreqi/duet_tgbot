# ===== Базовый образ Python =====
FROM python:3.11-slim

# ===== Рабочая директория =====
WORKDIR /app

# ===== Копируем зависимости =====
COPY requirements.txt .

# ===== Устанавливаем зависимости =====
RUN pip install --no-cache-dir -r requirements.txt

# ===== Копируем весь проект =====
COPY . .

# ===== Автоперезапуск при падении =====
CMD while true; do \
    echo "[`date '+%d.%m.%Y %H:%M:%S'`] 🚀 Запуск бота..."; \
    python bot.py || echo "[`date '+%d.%m.%Y %H:%M:%S'`] ⚠️ Бот упал, перезапуск через 5 секунд..."; \
    sleep 5; \
done
