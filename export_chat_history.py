#!/usr/bin/env python3
"""
Скрипт для выгрузки истории чатов за последние несколько дней
"""

import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import os
from config import DatabaseConfig

def export_chat_history(days=7):
    """
    Экспортирует историю чатов за указанное количество дней
    """
    try:
        # Подключение к базе данных
        conn = sqlite3.connect(DatabaseConfig.DB_PATH)
        cursor = conn.cursor()
        
        # Вычисляем дату начала периода
        start_date = datetime.now() - timedelta(days=days)
        start_date_str = start_date.strftime('%Y-%m-%d')
        
        print(f"📊 Выгружаю историю чатов за последние {days} дней (с {start_date_str})")
        print("=" * 60)
        
        # Запрос для получения всех сообщений за период
        query = """
        SELECT 
            u.username,
            u.telegram_id,
            m.role,
            m.message,
            m.created_at,
            DATE(m.created_at) as message_date
        FROM messages m
        JOIN users u ON m.user_id = u.id
        WHERE DATE(m.created_at) >= ?
        ORDER BY m.created_at DESC
        """
        
        cursor.execute(query, (start_date_str,))
        messages = cursor.fetchall()
        
        if not messages:
            print("❌ Нет сообщений за указанный период")
            return
        
        # Создаем DataFrame для удобной работы с данными
        df = pd.DataFrame(messages, columns=[
            'username', 'telegram_id', 'role', 'message', 'created_at', 'message_date'
        ])
        
        # Статистика по дням
        print("📈 Статистика по дням:")
        daily_stats = df.groupby(['message_date', 'role']).size().unstack(fill_value=0)
        for date in daily_stats.index:
            user_msgs = daily_stats.loc[date, 'user'] if 'user' in daily_stats.columns else 0
            bot_msgs = daily_stats.loc[date, 'assistant'] if 'assistant' in daily_stats.columns else 0
            print(f"   📅 {date}: 👤 {user_msgs} пользователей, 🤖 {bot_msgs} ответов бота")
        
        print()
        
        # Статистика по пользователям
        print("👥 Активность пользователей:")
        user_stats = df[df['role'] == 'user'].groupby(['username', 'telegram_id']).size().sort_values(ascending=False)
        for (username, telegram_id), count in user_stats.head(10).items():
            user_info = f"@{username}" if username else f"User {telegram_id}"
            print(f"   👤 {user_info} (TG ID: {telegram_id}): {count} сообщений")
        
        print()
        
        # Экспорт в Excel
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        excel_filename = f"chat_history_{days}days_{timestamp}.xlsx"
        
        with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
            # Лист с полной историей
            df_export = df.copy()
            df_export['user_info'] = df_export.apply(
                lambda row: f"@{row['username']}" if row['username'] else f"User {row['telegram_id']}", 
                axis=1
            )
            df_export = df_export[['user_info', 'telegram_id', 'role', 'message', 'created_at']]
            df_export.to_excel(writer, sheet_name='Полная история', index=False)
            
            # Лист со статистикой по дням
            daily_stats.to_excel(writer, sheet_name='Статистика по дням')
            
            # Лист со статистикой по пользователям
            user_stats_df = user_stats.reset_index()
            user_stats_df['user_info'] = user_stats_df.apply(
                lambda row: f"@{row['username']}" if row['username'] else f"User {row['telegram_id']}", 
                axis=1
            )
            user_stats_df = user_stats_df[['user_info', 'telegram_id', 0]]
            user_stats_df.columns = ['Пользователь', 'Telegram ID', 'Количество сообщений']
            user_stats_df.to_excel(writer, sheet_name='Активность пользователей', index=False)
        
        print(f"✅ История чатов экспортирована в файл: {excel_filename}")
        print(f"📊 Всего сообщений: {len(messages)}")
        print(f"👥 Уникальных пользователей: {df['telegram_id'].nunique()}")
        
        # Показываем последние 10 сообщений
        print("\n💬 Последние 10 сообщений:")
        print("-" * 80)
        
        for _, msg in df.head(10).iterrows():
            role_emoji = "👤" if msg['role'] == 'user' else "🤖"
            user_info = f"@{msg['username']}" if msg['username'] else f"User {msg['telegram_id']}"
            short_content = msg['message'][:100] + "..." if len(msg['message']) > 100 else msg['message']
            
            print(f"{role_emoji} [{msg['created_at']}] {user_info}")
            print(f"   💬 {short_content}")
            print("-" * 40)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при экспорте истории чатов: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Можно изменить количество дней
    days_to_export = 7  # По умолчанию 7 дней
    
    print("🔄 Запуск экспорта истории чатов...")
    export_chat_history(days_to_export)