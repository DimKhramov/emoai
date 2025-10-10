#!/usr/bin/env python3
"""
Скрипт для удаления тестовых аккаунтов из базы данных
"""

import sqlite3
from config import DatabaseConfig

def delete_test_accounts():
    """
    Удаляет тестовые аккаунты из базы данных
    """
    connection = sqlite3.connect(DatabaseConfig.DB_PATH, timeout=10.0)
    cursor = connection.cursor()
    
    # Список тестовых аккаунтов для удаления
    test_accounts = [
        'test_user',
        'test_user_2', 
        'test_user_3',
        'test_user_999999999'
    ]
    
    test_telegram_ids = [
        999999998,  # @test_user
        999999997,  # @test_user_2
        999999996,  # @test_user_3
        999999999   # @test_user_999999999
    ]
    
    print("🗑️ Удаление тестовых аккаунтов...")
    print("=" * 50)
    
    # Сначала показываем, что будем удалять
    for username in test_accounts:
        cursor.execute("SELECT id, username, telegram_id FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user:
            print(f"📋 Найден тестовый аккаунт: @{user[1]} (ID: {user[0]}, Telegram ID: {user[2]})")
    
    # Удаляем сообщения тестовых пользователей
    print("\n🗑️ Удаление сообщений тестовых пользователей...")
    for telegram_id in test_telegram_ids:
        # Получаем user_id по telegram_id
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        user = cursor.fetchone()
        if user:
            user_id = user[0]
            # Удаляем сообщения
            cursor.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
            deleted_messages = cursor.rowcount
            if deleted_messages > 0:
                print(f"   ✅ Удалено {deleted_messages} сообщений для пользователя с ID {user_id}")
    
    # Удаляем самих пользователей
    print("\n🗑️ Удаление тестовых пользователей...")
    total_deleted = 0
    
    for username in test_accounts:
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        if cursor.rowcount > 0:
            print(f"   ✅ Удален пользователь: @{username}")
            total_deleted += cursor.rowcount
    
    # Также удаляем по telegram_id на случай, если username отличается
    for telegram_id in test_telegram_ids:
        cursor.execute("SELECT username FROM users WHERE telegram_id = ?", (telegram_id,))
        user = cursor.fetchone()
        if user:
            cursor.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
            if cursor.rowcount > 0:
                print(f"   ✅ Удален пользователь с Telegram ID: {telegram_id}")
                total_deleted += cursor.rowcount
    
    connection.commit()
    connection.close()
    
    print("\n" + "=" * 50)
    print(f"✅ Операция завершена! Удалено пользователей: {total_deleted}")
    
    # Показываем обновленную статистику
    print("\n📊 Обновленная статистика:")
    connection = sqlite3.connect(DatabaseConfig.DB_PATH, timeout=10.0)
    cursor = connection.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM messages")
    total_messages = cursor.fetchone()[0]
    
    print(f"   👥 Всего пользователей: {total_users}")
    print(f"   💬 Всего сообщений: {total_messages}")
    
    connection.close()

if __name__ == "__main__":
    delete_test_accounts()