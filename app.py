#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главный файл запуска Telegram бота "Эмо-друг".
"""

import asyncio
import logging
import signal
from integrations.telegram import main as telegram_main, bot
from services.scheduler import DailyReminderScheduler
from config import SchedulerConfig, LoggingConfig

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LoggingConfig.LOG_LEVEL),
    format=LoggingConfig.LOG_FORMAT
)

logger = logging.getLogger(__name__)

# Глобальная переменная для планировщика
scheduler = None

async def start_application():
    """Запуск приложения с планировщиком"""
    global scheduler
    
    # Инициализация планировщика
    if SchedulerConfig.ENABLE_DAILY_REMINDERS:
        scheduler = DailyReminderScheduler(bot)
        scheduler.start(SchedulerConfig.DAILY_REMINDER_TIME)
        logger.info("Планировщик ежедневных уведомлений запущен")
    
    # Запуск основного приложения
    await telegram_main()

def stop_application():
    """Остановка приложения"""
    global scheduler
    if scheduler:
        scheduler.stop()
        logger.info("Планировщик остановлен")

if __name__ == "__main__":
    logger.info("Запуск Telegram бота 'Эмо-друг'...")
    try:
        asyncio.run(start_application())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
        stop_application()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        stop_application()