#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime, date, timedelta
from config import DatabaseConfig, SchedulerConfig

def check_scheduler_status():
    """Проверяет статус планировщика и отправленные уведомления"""
    
    # Подключение к базе данных
    conn = sqlite3.connect(DatabaseConfig.DB_PATH)
    cursor = conn.cursor()
    
    print("🤖 Статус планировщика уведомлений")
    print("=" * 60)
    
    # Проверяем настройки планировщика
    print(f"⏰ Время ежедневных уведомлений: {SchedulerConfig.DAILY_REMINDER_TIME}")
    print(f"🔔 Уведомления включены: {SchedulerConfig.ENABLE_DAILY_REMINDERS}")
    print(f"🌍 Часовой пояс: {SchedulerConfig.TIMEZONE}")
    print("-" * 60)
    
    # Получаем сегодняшнюю дату
    today = date.today().strftime('%Y-%m-%d')
    
    # Проверяем, отправлялись ли уведомления сегодня в назначенное время
    reminder_time = SchedulerConfig.DAILY_REMINDER_TIME
    reminder_datetime = f"{today} {reminder_time.hour:02d}:{reminder_time.minute:02d}"
    
    print(f"📅 Проверка уведомлений за {today}")
    print(f"🕐 Ожидаемое время отправки: {reminder_datetime}")
    
    # Ищем сообщения от бота в районе времени уведомлений (±30 минут)
    start_time = f"{today} {reminder_time.hour:02d}:{max(0, reminder_time.minute-30):02d}"
    end_time = f"{today} {reminder_time.hour:02d}:{min(59, reminder_time.minute+30):02d}"
    
    cursor.execute("""
    SELECT user_id, message, created_at
    FROM messages 
    WHERE role = 'assistant' 
    AND created_at BETWEEN ? AND ?
    ORDER BY created_at ASC
    """, (start_time, end_time))
    
    reminder_messages = cursor.fetchall()
    
    if reminder_messages:
        print(f"✅ Найдено {len(reminder_messages)} сообщений от бота в период уведомлений")
        print("\n📝 Отправленные уведомления:")
        
        for user_id, message, created_at in reminder_messages:
            short_message = message[:50] + "..." if len(message) > 50 else message
            print(f"   👤 Пользователь {user_id}: [{created_at}] {short_message}")
            
    else:
        print("❌ Уведомления в назначенное время не найдены")
        
        # Проверяем, есть ли вообще сообщения от бота сегодня
        cursor.execute("""
        SELECT COUNT(*) FROM messages 
        WHERE role = 'assistant' AND DATE(created_at) = ?
        """, (today,))
        
        bot_messages_today = cursor.fetchone()[0]
        print(f"📊 Всего сообщений от бота сегодня: {bot_messages_today}")
    
    # Проверяем общее количество пользователей
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM messages")
    total_users = cursor.fetchone()[0]
    
    print(f"\n👥 Всего пользователей в базе: {total_users}")
    
    # Проверяем активных пользователей за последние 7 дней
    week_ago = (date.today() - timedelta(days=7)).strftime('%Y-%m-%d')
    cursor.execute("""
    SELECT COUNT(DISTINCT user_id) FROM messages 
    WHERE role = 'user' AND DATE(created_at) >= ?
    """, (week_ago,))
    
    active_users_week = cursor.fetchone()[0]
    print(f"📈 Активных пользователей за неделю: {active_users_week}")
    
    # Проверяем последние уведомления по дням
    print(f"\n📊 История уведомлений за последние 7 дней:")
    
    for i in range(7):
        check_date = (date.today() - timedelta(days=i)).strftime('%Y-%m-%d')
        check_start = f"{check_date} {reminder_time.hour:02d}:{max(0, reminder_time.minute-30):02d}"
        check_end = f"{check_date} {reminder_time.hour:02d}:{min(59, reminder_time.minute+30):02d}"
        
        cursor.execute("""
        SELECT COUNT(*) FROM messages 
        WHERE role = 'assistant' 
        AND created_at BETWEEN ? AND ?
        """, (check_start, check_end))
        
        reminders_count = cursor.fetchone()[0]
        status = "✅" if reminders_count > 0 else "❌"
        print(f"   {status} {check_date}: {reminders_count} уведомлений")
    
    # Проверяем возможные проблемы
    print(f"\n🔍 Диагностика:")
    
    current_time = datetime.now().time()
    if current_time < reminder_time:
        print(f"   ⏳ Время уведомлений еще не наступило (сейчас {current_time.strftime('%H:%M')})")
    elif len(reminder_messages) == 0:
        print(f"   ⚠️  Уведомления не отправлены, возможные причины:")
        print(f"      - Планировщик не запущен")
        print(f"      - Ошибка в коде отправки")
        print(f"      - Проблемы с Telegram API")
    elif len(reminder_messages) < total_users:
        blocked_users = total_users - len(reminder_messages)
        print(f"   ⚠️  Уведомления отправлены не всем пользователям")
        print(f"      Возможно {blocked_users} пользователей заблокировали бота")
    else:
        print(f"   ✅ Планировщик работает корректно")
    
    conn.close()

if __name__ == "__main__":
    check_scheduler_status()