#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ручная отправка уведомлений всем пользователям
"""

import asyncio
import logging
from datetime import datetime
from integrations.telegram import bot
from services.scheduler import DailyReminderScheduler
from storage.db import get_all_users

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def send_manual_reminders():
    """Ручная отправка уведомлений всем пользователям"""
    print("=== РУЧНАЯ ОТПРАВКА УВЕДОМЛЕНИЙ ===")
    print(f"Время отправки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Получаем всех пользователей
    users = get_all_users()
    print(f"Найдено пользователей: {len(users)}")
    
    if not users:
        print("❌ Нет пользователей для отправки уведомлений")
        return
    
    # Создаем планировщик для использования его функций
    scheduler = DailyReminderScheduler(bot)
    
    print("\n🚀 Начинаем отправку уведомлений...")
    print("-" * 50)
    
    # Отправляем уведомления
    await scheduler.send_daily_reminders()
    
    print("-" * 50)
    print("✅ Отправка завершена!")
    print()
    print("=== ГОТОВО ===")

if __name__ == "__main__":
    asyncio.run(send_manual_reminders())