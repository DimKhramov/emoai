# Конфигурация приложения

import os
from datetime import time
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Telegram Bot настройки
TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")

# OpenAI настройки
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Настройки планировщика уведомлений
class SchedulerConfig:
    # Время отправки ежедневных напоминаний (по умолчанию 10:00)
    DAILY_REMINDER_TIME = time(
        hour=int(os.getenv("REMINDER_HOUR", "10")),
        minute=int(os.getenv("REMINDER_MINUTE", "0"))
    )
    
    # Включить/выключить ежедневные напоминания
    ENABLE_DAILY_REMINDERS = os.getenv("ENABLE_DAILY_REMINDERS", "true").lower() == "true"
    
    # Часовой пояс для планировщика
    TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")

# Настройки базы данных
class DatabaseConfig:
    DB_PATH = "database.sqlite"

# Настройки логирования
class LoggingConfig:
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"