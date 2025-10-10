#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime, timedelta
from config import DatabaseConfig

def check_recent_messages():
    """Проверяет последние сообщения в базе данных"""
    
    print("🔍 Проверка последних сообщений")
    print("=" * 60)
    
    conn = sqlite3.connect(DatabaseConfig.DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Получаем последние 20 сообщений
        query = """
        SELECT 
            m.id,
            m.user_id,
            u.username,
            u.telegram_id,
            m.role,
            m.message,
            m.created_at
        FROM messages m
        JOIN users u ON m.user_id = u.id
        ORDER BY m.created_at DESC
        LIMIT 20
        """
        
        cursor.execute(query)
        messages = cursor.fetchall()
        
        print(f"📝 Последние {len(messages)} сообщений:")
        print("-" * 60)
        
        for msg in messages:
            msg_id, user_id, username, telegram_id, role, content, created_at = msg
            
            role_emoji = "👤" if role == 'user' else "🤖"
            user_info = f"@{username}" if username else f"User {telegram_id}"
            
            # Обрезаем длинные сообщения
            short_content = content[:80] + "..." if len(content) > 80 else content
            
            print(f"{role_emoji} [{created_at}] {user_info} (TG ID: {telegram_id})")
            print(f"   💬 {short_content}")
            print("-" * 40)
        
        # Проверяем сообщения за последние 30 минут
        print(f"\n🕐 Сообщения за последние 30 минут:")
        
        # Время 30 минут назад
        thirty_min_ago = datetime.now() - timedelta(minutes=30)
        
        query_recent = """
        SELECT 
            u.username,
            u.telegram_id,
            m.role,
            m.message,
            m.created_at
        FROM messages m
        JOIN users u ON m.user_id = u.id
        WHERE m.created_at >= ?
        ORDER BY m.created_at DESC
        """
        
        cursor.execute(query_recent, (thirty_min_ago.strftime('%Y-%m-%d %H:%M:%S'),))
        recent_messages = cursor.fetchall()
        
        if recent_messages:
            for msg in recent_messages:
                username, telegram_id, role, content, created_at = msg
                
                role_emoji = "👤" if role == 'user' else "🤖"
                user_info = f"@{username}" if username else f"User {telegram_id}"
                
                short_content = content[:100] + "..." if len(content) > 100 else content
                
                print(f"   {role_emoji} [{created_at}] {user_info} (TG ID: {telegram_id})")
                print(f"      💬 {short_content}")
        else:
            print("   Нет сообщений за последние 30 минут")
        
        # Статистика активности сегодня
        print(f"\n📊 Активность сегодня:")
        today = datetime.now().strftime('%Y-%m-%d')
        
        query_today = """
        SELECT 
            u.username,
            u.telegram_id,
            COUNT(*) as message_count,
            MAX(m.created_at) as last_message
        FROM messages m
        JOIN users u ON m.user_id = u.id
        WHERE DATE(m.created_at) = ? AND m.role = 'user'
        GROUP BY u.id
        ORDER BY message_count DESC
        """
        
        cursor.execute(query_today, (today,))
        today_stats = cursor.fetchall()
        
        if today_stats:
            for user in today_stats:
                username, telegram_id, msg_count, last_msg = user
                user_info = f"@{username}" if username else f"User {telegram_id}"
                
                print(f"   👤 {user_info} (TG ID: {telegram_id})")
                print(f"      💬 {msg_count} сообщений, последнее: {last_msg}")
        else:
            print("   Нет активности сегодня")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке сообщений: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    check_recent_messages()