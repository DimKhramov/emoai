#!/usr/bin/env python3
"""
Скрипт для проверки активности пользователей бота
"""

import sqlite3
from datetime import datetime, timedelta
from config import DatabaseConfig

def get_recent_users(days=7):
    """Получить пользователей, зарегистрированных за последние N дней"""
    connection = sqlite3.connect(DatabaseConfig.DB_PATH)
    cursor = connection.cursor()
    
    # Дата N дней назад
    cutoff_date = datetime.now() - timedelta(days=days)
    
    cursor.execute("""
        SELECT id, username, telegram_id, created_at, 
               daily_message_count, last_message_date
        FROM users 
        WHERE created_at >= ? 
        ORDER BY created_at DESC
    """, (cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),))
    
    users = cursor.fetchall()
    connection.close()
    
    return users

def get_active_users(days=7):
    """Получить пользователей, которые писали за последние N дней"""
    connection = sqlite3.connect(DatabaseConfig.DB_PATH)
    cursor = connection.cursor()
    
    # Дата N дней назад
    cutoff_date = datetime.now() - timedelta(days=days)
    
    cursor.execute("""
        SELECT id, username, telegram_id, created_at, 
               daily_message_count, last_message_date
        FROM users 
        WHERE last_message_date >= ? 
        ORDER BY last_message_date DESC
    """, (cutoff_date.strftime('%Y-%m-%d'),))
    
    users = cursor.fetchall()
    connection.close()
    
    return users

def get_all_users_stats():
    """Получить общую статистику по всем пользователям"""
    connection = sqlite3.connect(DatabaseConfig.DB_PATH)
    cursor = connection.cursor()
    
    # Общее количество пользователей
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    # Пользователи с премиум
    cursor.execute("SELECT COUNT(*) FROM users WHERE premium_status = 1")
    premium_users = cursor.fetchone()[0]
    
    # Пользователи за последние 7 дней
    cutoff_date = datetime.now() - timedelta(days=7)
    cursor.execute("SELECT COUNT(*) FROM users WHERE created_at >= ?", 
                   (cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),))
    recent_users = cursor.fetchone()[0]
    
    # Активные пользователи за последние 7 дней
    cursor.execute("SELECT COUNT(*) FROM users WHERE last_message_date >= ?", 
                   (cutoff_date.strftime('%Y-%m-%d'),))
    active_users = cursor.fetchone()[0]
    
    connection.close()
    
    return {
        'total_users': total_users,
        'premium_users': premium_users,
        'recent_users': recent_users,
        'active_users': active_users
    }

if __name__ == "__main__":
    print("=== Статистика пользователей бота ===\n")
    
    # Общая статистика
    stats = get_all_users_stats()
    print(f"📊 Общая статистика:")
    print(f"   Всего пользователей: {stats['total_users']}")
    print(f"   Премиум пользователей: {stats['premium_users']}")
    print(f"   Новых за 7 дней: {stats['recent_users']}")
    print(f"   Активных за 7 дней: {stats['active_users']}")
    print()
    
    # Новые пользователи за последние 7 дней
    recent_users = get_recent_users(7)
    print(f"👥 Новые пользователи за последние 7 дней ({len(recent_users)}):")
    if recent_users:
        for user in recent_users:
            username = user[1] or "Без username"
            created_at = user[3]
            print(f"   • {username} (ID: {user[2]}) - {created_at}")
    else:
        print("   Нет новых пользователей")
    print()
    
    # Активные пользователи за последние 7 дней
    active_users = get_active_users(7)
    print(f"💬 Активные пользователи за последние 7 дней ({len(active_users)}):")
    if active_users:
        for user in active_users:
            username = user[1] or "Без username"
            last_message = user[5] or "Неизвестно"
            message_count = user[4] or 0
            print(f"   • {username} (ID: {user[2]}) - последнее сообщение: {last_message}, сообщений сегодня: {message_count}")
    else:
        print("   Нет активных пользователей")