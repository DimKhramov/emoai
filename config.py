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
    # Время отправки ежедневных напоминаний (по умолчанию 15:30)
    DAILY_REMINDER_TIME = time(hour=14, minute=33)
    
    # Включить/выключить ежедневные напоминания
    ENABLE_DAILY_REMINDERS = True
    
    # Часовой пояс для планировщика
    TIMEZONE = "Europe/Moscow"
    
    # Время напоминаний о продлении подписки
    RENEWAL_REMINDER_HOUR = 11
    RENEWAL_REMINDER_MINUTE = 0
    
    # Время автоматического продления подписки
    AUTO_RENEWAL_HOUR = 12
    AUTO_RENEWAL_MINUTE = 0

# Настройки OpenAI
class OpenAIConfig:
    MODEL = "gpt-4o-mini"
    MAX_TOKENS = 1000
    TEMPERATURE = 0.7
    TIMEOUT = 30.0

# Настройки лимитов
class LimitsConfig:
    DAILY_MESSAGE_LIMIT = 20
    DEFAULT_SUBSCRIPTION_DAYS = 30
    # Лимит контекста для GPT анализа (количество последних сообщений)
    CONTEXT_MESSAGE_LIMIT = 15

# Настройки премиум подписки
class PremiumConfig:
    DAILY_PRICE = int(os.getenv("PREMIUM_DAILY_STARS", "10"))
    DAILY_DAYS = int(os.getenv("PREMIUM_DAILY_DAYS", "1"))
    
    WEEKLY_PRICE = int(os.getenv("PREMIUM_WEEKLY_STARS", "30"))
    WEEKLY_DAYS = int(os.getenv("PREMIUM_WEEKLY_DAYS", "7"))
    
    MONTHLY_PRICE = int(os.getenv("PREMIUM_MONTHLY_STARS", "100"))
    MONTHLY_DAYS = int(os.getenv("PREMIUM_MONTHLY_DAYS", "30"))



# Настройки базы данных
class DatabaseConfig:
    DB_PATH = os.getenv("DB_PATH", "storage/database.sqlite")

# Настройки логирования
class LoggingConfig:
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"