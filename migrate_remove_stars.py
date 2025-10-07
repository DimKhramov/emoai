#!/usr/bin/env python3
"""
Миграция для удаления поля stars_balance из базы данных
"""

import sqlite3
import os

DB_PATH = 'storage/database.db'

def migrate_remove_stars_balance():
    """Удаляет колонку stars_balance из таблицы users"""
    
    if not os.path.exists(DB_PATH):
        print("❌ База данных не найдена!")
        return False
    
    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        
        # Проверяем существование колонки
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'stars_balance' not in column_names:
            print("✅ Колонка stars_balance уже отсутствует в базе данных")
            connection.close()
            return True
        
        print("🔄 Начинаем миграцию...")
        
        # Создаем новую таблицу без stars_balance
        cursor.execute("""
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                created_at TEXT NOT NULL,
                premium_status BOOLEAN DEFAULT FALSE,
                subscription_end_date TEXT,
                auto_renewal BOOLEAN DEFAULT TRUE,
                subscription_type INTEGER DEFAULT 30
            )
        """)
        
        # Копируем данные из старой таблицы в новую (без stars_balance)
        cursor.execute("""
            INSERT INTO users_new (id, telegram_id, username, created_at, premium_status, subscription_end_date, auto_renewal, subscription_type)
            SELECT id, telegram_id, username, created_at, premium_status, subscription_end_date, auto_renewal, subscription_type
            FROM users
        """)
        
        # Удаляем старую таблицу
        cursor.execute("DROP TABLE users")
        
        # Переименовываем новую таблицу
        cursor.execute("ALTER TABLE users_new RENAME TO users")
        
        connection.commit()
        connection.close()
        
        print("✅ Миграция завершена успешно!")
        print("📊 Колонка stars_balance удалена из базы данных")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск миграции для удаления stars_balance...")
    success = migrate_remove_stars_balance()
    if success:
        print("🎉 Миграция выполнена успешно!")
    else:
        print("💥 Миграция не удалась!")