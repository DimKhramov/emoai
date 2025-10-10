#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отладка планировщика уведомлений
"""

import asyncio
import logging
from datetime import datetime, time
from integrations.telegram import bot
from services.scheduler import DailyReminderScheduler
from storage.db import get_all_users
from config import SchedulerConfig

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_scheduler():
    """Тестирование планировщика"""
    print("=== ОТЛАДКА ПЛАНИРОВЩИКА УВЕДОМЛЕНИЙ ===")
    print(f"Время: {datetime.now()}")
    print()
    
    # Проверяем настройки
    print("1. НАСТРОЙКИ ПЛАНИРОВЩИКА:")
    print(f"   Включены ли уведомления: {SchedulerConfig.ENABLE_DAILY_REMINDERS}")
    print(f"   Время уведомлений: {SchedulerConfig.DAILY_REMINDER_TIME}")
    print()
    
    # Проверяем пользователей
    print("2. ПОЛЬЗОВАТЕЛИ В БАЗЕ:")
    users = get_all_users()
    print(f"   Всего пользователей: {len(users)}")
    for i, user in enumerate(users[:5]):  # Показываем первых 5
        print(f"   {i+1}. ID: {user['telegram_id']}, Username: {user['username']}")
    if len(users) > 5:
        print(f"   ... и еще {len(users) - 5} пользователей")
    print()
    
    # Создаем планировщик
    print("3. СОЗДАНИЕ ПЛАНИРОВЩИКА:")
    scheduler = DailyReminderScheduler(bot)
    print("   Планировщик создан")
    
    # Проверяем отправку тестового уведомления
    print("4. ТЕСТ ОТПРАВКИ УВЕДОМЛЕНИЯ:")
    if users:
        test_user = users[0]  # Берем первого пользователя
        print(f"   Отправляем тестовое уведомление пользователю {test_user['telegram_id']}")
        try:
            success = await scheduler.send_test_reminder(test_user['telegram_id'])
            if success:
                print("   ✅ Тестовое уведомление отправлено успешно!")
            else:
                print("   ❌ Ошибка отправки тестового уведомления")
        except Exception as e:
            print(f"   ❌ Исключение при отправке: {e}")
    else:
        print("   Нет пользователей для тестирования")
    print()
    
    # Проверяем массовую отправку
    print("5. ТЕСТ МАССОВОЙ ОТПРАВКИ:")
    try:
        await scheduler.send_daily_reminders()
        print("   ✅ Функция массовой отправки выполнена")
    except Exception as e:
        print(f"   ❌ Ошибка массовой отправки: {e}")
    print()
    
    print("=== ОТЛАДКА ЗАВЕРШЕНА ===")

if __name__ == "__main__":
    asyncio.run(test_scheduler())