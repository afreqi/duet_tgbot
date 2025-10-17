# ===== Базовый образ Python =====
FROM python:3.11-slim

# ===== Рабочая директория =====
WORKDIR /app

# ===== Копируем файлы проекта =====
COPY . .

# ===== Устанавливаем зависимости =====
RUN pip install --no-cache-dir -r requirements.txt

# ===== Автоматический перезапуск =====
# Если бот завершится с ошибкой — Docker перезапустит процесс через 5 секунд
CMD ["bash", "-c", "while true; do python bot.py; echo '⚠️ Бот упал, перезапуск через 5 секунд...'; sleep 5; done"]
