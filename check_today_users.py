#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime, date
from collections import defaultdict

def check_today_users():
    """Проверяет активность пользователей за сегодня"""
    
    # Подключение к базе данных
    from config import DatabaseConfig
    conn = sqlite3.connect(DatabaseConfig.DB_PATH)
    cursor = conn.cursor()
    
    # Получаем сегодняшнюю дату
    today = date.today().strftime('%Y-%m-%d')
    
    print(f"📅 Активность пользователей за {today}")
    print("=" * 60)
    
    # Запрос для получения пользователей, которые писали сегодня
    query = """
    SELECT user_id, COUNT(*) as message_count,
           MIN(created_at) as first_message_today,
           MAX(created_at) as last_message_today
    FROM messages 
    WHERE DATE(created_at) = ? AND role = 'user'
    GROUP BY user_id
    ORDER BY message_count DESC
    """
    
    cursor.execute(query, (today,))
    active_users_today = cursor.fetchall()
    
    if active_users_today:
        print(f"👥 Активных пользователей сегодня: {len(active_users_today)}")
        print("-" * 60)
        
        total_messages_today = 0
        for user_id, msg_count, first_msg, last_msg in active_users_today:
            total_messages_today += msg_count
            print(f"👤 Пользователь ID: {user_id}")
            print(f"   💬 Сообщений сегодня: {msg_count}")
            print(f"   🕐 Первое сообщение: {first_msg}")
            print(f"   🕐 Последнее сообщение: {last_msg}")
            print("-" * 40)
        
        print(f"\n📊 Общая статистика за сегодня:")
        print(f"   👥 Активных пользователей: {len(active_users_today)}")
        print(f"   💬 Всего сообщений от пользователей: {total_messages_today}")
        
        # Получаем количество сообщений бота за сегодня
        cursor.execute("""
        SELECT COUNT(*) FROM messages 
        WHERE role = 'assistant' AND DATE(created_at) = ?
        """, (today,))
        bot_messages_today = cursor.fetchone()[0]
        
        print(f"   🤖 Сообщений от бота: {bot_messages_today}")
        print(f"   📈 Общая активность: {total_messages_today + bot_messages_today} сообщений")
        
        # Статистика по часам
        print(f"\n🕐 Активность по часам:")
        cursor.execute("""
        SELECT strftime('%H', created_at) as hour, COUNT(*) as count
        FROM messages 
        WHERE DATE(created_at) = ?
        GROUP BY hour
        ORDER BY hour
        """, (today,))
        
        hourly_stats = cursor.fetchall()
        for hour, count in hourly_stats:
            print(f"   {hour}:00 - {count} сообщений")
            
    else:
        print("😴 Сегодня пока никто не писал боту")
    
    # Проверяем новых пользователей за сегодня
    cursor.execute("""
    SELECT user_id, MIN(created_at) as first_message
    FROM messages 
    WHERE DATE(created_at) = ? AND role = 'user'
    GROUP BY user_id
    HAVING MIN(DATE(created_at)) = ?
    """, (today, today))
    
    new_users_today = cursor.fetchall()
    
    if new_users_today:
        print(f"\n🆕 Новые пользователи сегодня: {len(new_users_today)}")
        print("-" * 40)
        for user_id, first_message in new_users_today:
            print(f"👤 ID: {user_id} - первое сообщение: {first_message}")
    
    conn.close()

if __name__ == "__main__":
    check_today_users()