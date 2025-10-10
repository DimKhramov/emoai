#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime, date
from config import DatabaseConfig

def check_bot_messages_today():
    """Проверяет сообщения, которые бот отправил сегодня"""
    
    # Подключение к базе данных
    conn = sqlite3.connect(DatabaseConfig.DB_PATH)
    cursor = conn.cursor()
    
    # Получаем сегодняшнюю дату
    today = date.today().strftime('%Y-%m-%d')
    
    print(f"🤖 Сообщения бота за {today}")
    print("=" * 60)
    
    # Запрос для получения всех сообщений бота за сегодня
    query = """
    SELECT user_id, message, created_at
    FROM messages 
    WHERE DATE(created_at) = ? AND role = 'assistant'
    ORDER BY created_at ASC
    """
    
    cursor.execute(query, (today,))
    bot_messages_today = cursor.fetchall()
    
    if bot_messages_today:
        print(f"📊 Всего сообщений от бота сегодня: {len(bot_messages_today)}")
        print("-" * 60)
        
        # Группируем сообщения по пользователям
        messages_by_user = {}
        for user_id, message, created_at in bot_messages_today:
            if user_id not in messages_by_user:
                messages_by_user[user_id] = []
            messages_by_user[user_id].append((message, created_at))
        
        # Выводим сообщения для каждого пользователя
        for user_id, messages in messages_by_user.items():
            print(f"\n👤 Пользователь ID: {user_id}")
            print(f"   💬 Сообщений от бота: {len(messages)}")
            print("   📝 Сообщения:")
            
            for i, (message, created_at) in enumerate(messages, 1):
                # Обрезаем длинные сообщения для читаемости
                short_message = message[:100] + "..." if len(message) > 100 else message
                print(f"      {i}. [{created_at}] {short_message}")
            
            print("-" * 40)
        
        # Статистика по времени отправки
        print(f"\n🕐 Статистика по часам:")
        cursor.execute("""
        SELECT strftime('%H', created_at) as hour, COUNT(*) as count
        FROM messages 
        WHERE DATE(created_at) = ? AND role = 'assistant'
        GROUP BY hour
        ORDER BY hour
        """, (today,))
        
        hourly_stats = cursor.fetchall()
        for hour, count in hourly_stats:
            print(f"   {hour}:00 - {count} сообщений от бота")
        
        # Самые активные диалоги
        print(f"\n📈 Самые активные диалоги сегодня:")
        cursor.execute("""
        SELECT user_id, COUNT(*) as bot_messages
        FROM messages 
        WHERE DATE(created_at) = ? AND role = 'assistant'
        GROUP BY user_id
        ORDER BY bot_messages DESC
        """, (today,))
        
        active_dialogs = cursor.fetchall()
        for user_id, msg_count in active_dialogs:
            print(f"   👤 Пользователь {user_id}: {msg_count} ответов от бота")
            
    else:
        print("😴 Бот сегодня пока никому не отвечал")
    
    # Проверяем общую статистику диалогов за сегодня
    cursor.execute("""
    SELECT 
        COUNT(CASE WHEN role = 'user' THEN 1 END) as user_messages,
        COUNT(CASE WHEN role = 'assistant' THEN 1 END) as bot_messages,
        COUNT(DISTINCT user_id) as unique_users
    FROM messages 
    WHERE DATE(created_at) = ?
    """, (today,))
    
    stats = cursor.fetchone()
    user_msgs, bot_msgs, unique_users = stats
    
    print(f"\n📊 Общая статистика диалогов за сегодня:")
    print(f"   👥 Уникальных пользователей: {unique_users}")
    print(f"   💬 Сообщений от пользователей: {user_msgs}")
    print(f"   🤖 Ответов от бота: {bot_msgs}")
    
    if user_msgs > 0:
        response_rate = (bot_msgs / user_msgs) * 100
        print(f"   📈 Процент ответов бота: {response_rate:.1f}%")
    
    conn.close()

if __name__ == "__main__":
    check_bot_messages_today()