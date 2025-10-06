# Работа с SQLite

import sqlite3

DB_PATH = "database.sqlite"

def initialize_database():
    """
    Инициализация базы данных и создание таблиц.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Таблица пользователей
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            telegram_id INTEGER UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Таблица сообщений
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )

    # Таблица записей дневника
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mood INTEGER NOT NULL,
            facts TEXT,
            gratitude TEXT,
            plan TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )

    # Таблица настроек
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            value TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )

    connection.commit()
    connection.close()

def add_user(username: str, telegram_id: int) -> int:
    """
    Добавляет нового пользователя в базу данных.
    Возвращает ID пользователя или существующий ID если пользователь уже есть.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    # Проверяем, существует ли пользователь
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        connection.close()
        return existing_user[0]
    
    # Добавляем нового пользователя
    cursor.execute(
        "INSERT INTO users (username, telegram_id) VALUES (?, ?)",
        (username, telegram_id)
    )
    user_id = cursor.lastrowid
    connection.commit()
    connection.close()
    
    return user_id

def get_user_by_telegram_id(telegram_id: int) -> dict:
    """
    Получает данные пользователя по Telegram ID.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    cursor.execute(
        "SELECT id, username, created_at FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )
    user = cursor.fetchone()
    connection.close()
    
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'telegram_id': telegram_id,
            'created_at': user[2]
        }
    return None

def is_new_user(telegram_id: int) -> bool:
    """
    Проверяет, является ли пользователь новым (первый раз зашел).
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    connection.close()
    
    return user is None

def add_message(user_id: int, message: str, role: str = 'user'):
    """
    Добавляет сообщение в историю чата.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    cursor.execute(
        "INSERT INTO messages (user_id, message, role) VALUES (?, ?, ?)",
        (user_id, message, role)
    )
    connection.commit()
    connection.close()

def get_conversation_history(user_id: int, limit: int = 50) -> list:
    """
    Получает историю разговора пользователя.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    cursor.execute(
        "SELECT message, role, created_at FROM messages WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    )
    messages = cursor.fetchall()
    connection.close()
    
    # Возвращаем в обратном порядке (от старых к новым)
    return [{
        'content': msg[0],
        'role': msg[1],
        'timestamp': msg[2]
    } for msg in reversed(messages)]

def clear_conversation_history(user_id: int):
    """
    Очищает историю разговора пользователя.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    cursor.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
    connection.commit()
    connection.close()

def get_user_stats(user_id: int) -> dict:
    """
    Получает статистику пользователя.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM messages WHERE user_id = ?", (user_id,))
    message_count = cursor.fetchone()[0]
    
    cursor.execute(
        "SELECT created_at FROM messages WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
        (user_id,)
    )
    last_message = cursor.fetchone()
    last_activity = last_message[0] if last_message else None
    
    connection.close()
    
    return {
        'message_count': message_count,
        'last_activity': last_activity
    }

def get_all_users():
    """
    Получает всех пользователей из базы данных.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    cursor.execute("SELECT id, username, telegram_id, created_at FROM users")
    users = cursor.fetchall()
    connection.close()
    
    return [{
        'id': user[0],
        'username': user[1],
        'telegram_id': user[2],
        'created_at': user[3]
    } for user in users]

if __name__ == "__main__":
    initialize_database()