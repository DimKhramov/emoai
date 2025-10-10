#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка пользователей, которые заблокировали бота
"""

import asyncio
import logging
from integrations.telegram import bot
from storage.db import get_all_users
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

# Настройка логирования
logging.basicConfig(level=logging.WARNING)  # Убираем лишние логи
logger = logging.getLogger(__name__)

async def check_blocked_users():
    """Проверяем каких пользователей заблокировали бота"""
    print("=== ПРОВЕРКА ЗАБЛОКИРОВАННЫХ ПОЛЬЗОВАТЕЛЕЙ ===")
    print()
    
    users = get_all_users()
    print(f"Всего пользователей в базе: {len(users)}")
    print()
    
    blocked_users = []
    active_users = []
    
    print("Проверяем доступность пользователей...")
    
    for i, user in enumerate(users, 1):
        try:
            # Пытаемся получить информацию о чате
            chat_info = await bot.get_chat(user['telegram_id'])
            active_users.append({
                'telegram_id': user['telegram_id'],
                'username': user['username'],
                'first_name': getattr(chat_info, 'first_name', 'Не указано'),
                'last_name': getattr(chat_info, 'last_name', ''),
                'created_at': user['created_at']
            })
            print(f"  {i:2d}. ✅ {user['username'] or 'Без ника'} (ID: {user['telegram_id']})")
            
        except TelegramForbiddenError:
            # Пользователь заблокировал бота
            blocked_users.append({
                'telegram_id': user['telegram_id'],
                'username': user['username'],
                'created_at': user['created_at']
            })
            print(f"  {i:2d}. ❌ {user['username'] or 'Без ника'} (ID: {user['telegram_id']}) - ЗАБЛОКИРОВАЛ БОТА")
            
        except TelegramBadRequest as e:
            # Неверный chat_id или пользователь не найден
            blocked_users.append({
                'telegram_id': user['telegram_id'],
                'username': user['username'],
                'created_at': user['created_at'],
                'error': str(e)
            })
            print(f"  {i:2d}. ⚠️  {user['username'] or 'Без ника'} (ID: {user['telegram_id']}) - ОШИБКА: {e}")
            
        except Exception as e:
            print(f"  {i:2d}. ❓ {user['username'] or 'Без ника'} (ID: {user['telegram_id']}) - НЕИЗВЕСТНАЯ ОШИБКА: {e}")
        
        # Небольшая задержка между запросами
        await asyncio.sleep(0.1)
    
    print()
    print("=== РЕЗУЛЬТАТЫ ===")
    print(f"✅ Активных пользователей: {len(active_users)}")
    print(f"❌ Заблокированных/недоступных: {len(blocked_users)}")
    print()
    
    if blocked_users:
        print("🚫 ЗАБЛОКИРОВАННЫЕ ПОЛЬЗОВАТЕЛИ:")
        for i, user in enumerate(blocked_users, 1):
            username_display = f"@{user['username']}" if user['username'] else "Без ника"
            error_info = f" ({user.get('error', 'заблокировал бота')})" if 'error' in user else ""
            print(f"  {i}. {username_display} (ID: {user['telegram_id']}) - {user['created_at']}{error_info}")
    else:
        print("🎉 Все пользователи активны!")
    
    print()
    print("=== ПРОВЕРКА ЗАВЕРШЕНА ===")

if __name__ == "__main__":
    asyncio.run(check_blocked_users())