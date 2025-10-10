#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def check_db_structure():
    """Проверяет структуру базы данных"""
    
    db_path = 'user_data/chat_history.db'
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return
    
    print(f"📊 Проверка структуры базы данных: {db_path}")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Получаем список всех таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"📋 Найдено таблиц: {len(tables)}")
    print("-" * 40)
    
    for table in tables:
        table_name = table[0]
        print(f"\n📊 Таблица: {table_name}")
        
        # Получаем структуру таблицы
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        print("   Колонки:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # Получаем количество записей
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"   📈 Записей: {count}")
        
        # Показываем несколько примеров записей
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            samples = cursor.fetchall()
            print("   📝 Примеры записей:")
            for i, sample in enumerate(samples, 1):
                print(f"      {i}. {sample}")
    
    conn.close()

if __name__ == "__main__":
    check_db_structure()