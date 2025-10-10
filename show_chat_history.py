#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для просмотра истории всех чатов
"""

import sys
import os
from datetime import datetime

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
from config import DatabaseConfig

def show_all_chat_history():
    """Показать историю всех чатов"""
    
    print("📚 История всех чатов с ботом EmoAi")
    print("=" * 60)
    
    conn = sqlite3.connect(DatabaseConfig.DB_PATH, timeout=10.0)
    cursor = conn.cursor()
    
    try:
        # Получаем всех пользователей с их сообщениями
        query = """
        SELECT 
            u.telegram_id,
            u.username,
            COUNT(m.id) as message_count,
            MIN(m.created_at) as first_message,
            MAX(m.created_at) as last_message
        FROM users u
        LEFT JOIN messages m ON u.id = m.user_id
        GROUP BY u.id, u.telegram_id, u.username
        ORDER BY last_message DESC NULLS LAST
        """
        
        cursor.execute(query)
        users = cursor.fetchall()
        
        print(f"👥 Всего пользователей: {len(users)}")
        print("-" * 60)
        
        for row in users:
            telegram_id, username, message_count, first_message, last_message = row
            
            print(f"👤 Пользователь: @{username or 'неизвестно'}")
            print(f"   📱 Telegram ID: {telegram_id}")
            print(f"   💬 Сообщений: {message_count}")
            
            if first_message:
                print(f"   📅 Первое сообщение: {first_message}")
            if last_message:
                print(f"   📅 Последнее сообщение: {last_message}")
            
            # Показываем последние сообщения этого пользователя
            if message_count > 0:
                print(f"   📝 Последние сообщения:")
                
                msg_query = """
                SELECT role, message, created_at 
                FROM messages 
                WHERE user_id = (SELECT id FROM users WHERE telegram_id = ?)
                ORDER BY created_at DESC 
                LIMIT 10
                """
                
                cursor.execute(msg_query, (telegram_id,))
                messages = cursor.fetchall()
                
                for msg_role, msg_content, msg_time in messages:
                    role_emoji = "👤" if msg_role == 'user' else "🤖"
                    # Обрезаем длинные сообщения
                    content = msg_content[:100] + "..." if len(msg_content) > 100 else msg_content
                    print(f"      {role_emoji} [{msg_time}] {content}")
            
            print("-" * 40)
        
        # Статистика по сообщениям
        print(f"\n📊 Общая статистика:")
        
        # Общее количество сообщений
        cursor.execute("SELECT COUNT(*) FROM messages")
        total_messages = cursor.fetchone()[0]
        print(f"   Всего сообщений: {total_messages}")
        
        # Сообщения пользователей vs бота
        cursor.execute("SELECT role, COUNT(*) FROM messages GROUP BY role")
        role_stats = cursor.fetchall()
        for role, count in role_stats:
            role_name = "Пользователи" if role == 'user' else "Бот"
            print(f"   {role_name}: {count}")
        
        # Активность по дням
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count 
            FROM messages 
            GROUP BY DATE(created_at) 
            ORDER BY date DESC 
            LIMIT 7
        """)
        daily_stats = cursor.fetchall()
        
        if daily_stats:
            print(f"\n📅 Активность за последние дни:")
            for date, count in daily_stats:
                print(f"   {date}: {count} сообщений")
        
    except Exception as e:
        print(f"❌ Ошибка при получении истории: {e}")
    
    finally:
        conn.close()

def show_detailed_chat(telegram_id):
    """Показать детальную историю конкретного чата"""
    
    print(f"💬 Детальная история чата с пользователем {telegram_id}")
    print("=" * 60)
    
    conn = sqlite3.connect(DatabaseConfig.DB_PATH, timeout=10.0)
    cursor = conn.cursor()
    
    try:
        # Получаем информацию о пользователе
        cursor.execute("""
            SELECT username, first_name, last_name 
            FROM users 
            WHERE telegram_id = ?
        """, (telegram_id,))
        
        user_info = cursor.fetchone()
        if not user_info:
            print(f"❌ Пользователь с ID {telegram_id} не найден")
            return
        
        username, first_name, last_name = user_info
        print(f"👤 Пользователь: {first_name} {last_name} (@{username})")
        
        # Получаем все сообщения
        cursor.execute("""
            SELECT role, message, created_at 
            FROM messages 
            WHERE user_id = (SELECT id FROM users WHERE telegram_id = ?)
            ORDER BY created_at ASC
        """, (telegram_id,))
        
        messages = cursor.fetchall()
        
        print(f"📝 Всего сообщений: {len(messages)}")
        print("-" * 60)
        
        for i, (role, content, timestamp) in enumerate(messages, 1):
            role_emoji = "👤" if role == 'user' else "🤖"
            role_name = "Пользователь" if role == 'user' else "EmoAi"
            
            print(f"{i:3d}. {role_emoji} [{timestamp}] {role_name}:")
            print(f"     {content}")
            print()
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Если передан telegram_id, показываем детальную историю
        try:
            telegram_id = int(sys.argv[1])
            show_detailed_chat(telegram_id)
        except ValueError:
            print("❌ Неверный формат Telegram ID")
    else:
        # Показываем общую историю всех чатов
        show_all_chat_history()