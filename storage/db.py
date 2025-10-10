# Работа с SQLite

import sqlite3
from config import DatabaseConfig, LimitsConfig

DB_PATH = DatabaseConfig.DB_PATH

def initialize_database():
    """
    Инициализация базы данных и создание таблиц.
    """
    connection = sqlite3.connect(DB_PATH, timeout=10.0)
    connection.execute("PRAGMA journal_mode=WAL")
    cursor = connection.cursor()

    # Таблица пользователей
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            telegram_id INTEGER UNIQUE NOT NULL,
            daily_message_count INTEGER DEFAULT 0,
            last_message_date DATE DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    
    # Добавляем новые поля в существующую таблицу, если их нет
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN daily_message_count INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Поле уже существует
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN last_message_date DATE DEFAULT NULL")
    except sqlite3.OperationalError:
        pass  # Поле уже существует
    
    # Добавляем поля для системы оплаты через Telegram Stars
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN premium_status BOOLEAN DEFAULT FALSE")
    except sqlite3.OperationalError:
        pass  # Поле уже существует
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN stars_balance INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Поле уже существует
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN subscription_end_date DATE DEFAULT NULL")
    except sqlite3.OperationalError:
        pass  # Поле уже существует
    
    # Добавляем поле для автоматических платежей
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN auto_renewal BOOLEAN DEFAULT FALSE")
    except sqlite3.OperationalError:
        pass  # Поле уже существует
    
    # Добавляем поле для типа подписки (дни подписки)
    try:
        cursor.execute(f"ALTER TABLE users ADD COLUMN subscription_type INTEGER DEFAULT {LimitsConfig.DEFAULT_SUBSCRIPTION_DAYS}")
    except sqlite3.OperationalError:
        pass  # Поле уже существует
    
    # Добавляем поля для пользовательских предпочтений
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN use_emojis BOOLEAN DEFAULT TRUE")
    except sqlite3.OperationalError:
        pass  # Поле уже существует
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN communication_style TEXT DEFAULT 'friendly'")
    except sqlite3.OperationalError:
        pass  # Поле уже существует
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN preferred_response_length TEXT DEFAULT 'medium'")
    except sqlite3.OperationalError:
        pass  # Поле уже существует

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
    connection = sqlite3.connect(DB_PATH, timeout=10.0)
    connection.execute("PRAGMA journal_mode=WAL")
    cursor = connection.cursor()
    
    try:
        # Проверяем, существует ли пользователь
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            return existing_user[0]
        
        # Добавляем нового пользователя
        cursor.execute(
            "INSERT INTO users (username, telegram_id, created_at) VALUES (?, ?, datetime('now'))",
            (username, telegram_id)
        )
        user_id = cursor.lastrowid
        connection.commit()
        
        return user_id
    except sqlite3.OperationalError as e:
        print(f"Database error in add_user: {e}")
        # Возвращаем 0 в случае ошибки, чтобы не ломать логику
        return 0
    finally:
        connection.close()

def get_user_by_telegram_id(telegram_id: int) -> dict:
    """
    Получает данные пользователя по Telegram ID.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    cursor.execute(
        "SELECT id, username, created_at, premium_status, subscription_end_date, auto_renewal, subscription_type, use_emojis, communication_style, preferred_response_length FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )
    user = cursor.fetchone()
    connection.close()
    
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'telegram_id': telegram_id,
            'created_at': user[2],
            'premium_status': bool(user[3]) if user[3] is not None else False,
            'subscription_end_date': user[4],
            'auto_renewal': bool(user[5]) if user[5] is not None else False,
            'subscription_type': user[6] or LimitsConfig.DEFAULT_SUBSCRIPTION_DAYS,
            'use_emojis': bool(user[7]) if user[7] is not None else True,
            'communication_style': user[8] or 'friendly',
            'preferred_response_length': user[9] or 'medium'
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

def check_daily_message_limit(telegram_id: int, limit: int = None) -> bool:
    """
    Проверяет, не превышен ли дневной лимит сообщений для пользователя.
    
    Args:
        telegram_id: ID пользователя в Telegram
        limit: Максимальное количество сообщений в день (по умолчанию из конфигурации)
    
    Returns:
        True если лимит не превышен, False если превышен
    """
    # Сначала проверяем премиум статус
    premium_info = get_user_premium_status(telegram_id)
    if premium_info and premium_info['premium_status']:
        return True  # Премиум пользователи имеют безлимитный доступ
    
    if limit is None:
        limit = LimitsConfig.DAILY_MESSAGE_LIMIT
    from datetime import date
    
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    today = date.today().isoformat()
    
    cursor.execute(
        "SELECT daily_message_count, last_message_date FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )
    result = cursor.fetchone()
    
    if not result:
        connection.close()
        return True  # Пользователь не найден, разрешаем
    
    daily_count, last_date = result
    
    # Если это новый день, сбрасываем счетчик
    if last_date != today:
        daily_count = 0
    
    connection.close()
    return daily_count < limit

def increment_daily_message_count(telegram_id: int):
    """
    Увеличивает счетчик ежедневных сообщений пользователя.
    
    Args:
        telegram_id: ID пользователя в Telegram
    """
    from datetime import date
    
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    today = date.today().isoformat()
    
    cursor.execute(
        "SELECT daily_message_count, last_message_date FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )
    result = cursor.fetchone()
    
    if result:
        daily_count, last_date = result
        
        # Если это новый день, сбрасываем счетчик
        if last_date != today:
            daily_count = 0
        
        # Увеличиваем счетчик и обновляем дату
        new_count = daily_count + 1
        cursor.execute(
            "UPDATE users SET daily_message_count = ?, last_message_date = ? WHERE telegram_id = ?",
            (new_count, today, telegram_id)
        )
    
    connection.commit()
    connection.close()

def get_daily_message_count(telegram_id: int) -> int:
    """
    Получает текущий счетчик ежедневных сообщений пользователя.
    
    Args:
        telegram_id: ID пользователя в Telegram
    
    Returns:
        Количество сообщений за сегодня
    """
    from datetime import date
    
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    today = date.today().isoformat()
    
    cursor.execute(
        "SELECT daily_message_count, last_message_date FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )
    result = cursor.fetchone()
    
    if not result:
        connection.close()
        return 0
    
    daily_count, last_date = result
    
    # Если это новый день, счетчик равен 0
    if last_date != today:
        daily_count = 0
    
    connection.close()
    return daily_count

def get_user_premium_status(telegram_id: int) -> dict:
    """
    Получает информацию о премиум статусе пользователя.
    
    Args:
        telegram_id: ID пользователя в Telegram
    
    Returns:
        Словарь с информацией о премиум статусе
    """
    from datetime import date
    
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    cursor.execute(
        "SELECT premium_status, subscription_end_date, auto_renewal FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )
    result = cursor.fetchone()

    if not result:
        connection.close()
        return {"premium_status": False, "subscription_end_date": None, "auto_renewal": False}

    premium_status, subscription_end, auto_renewal = result
    
    # Проверяем, не истекла ли подписка
    if subscription_end:
        subscription_end_date = date.fromisoformat(subscription_end)
        if subscription_end_date < date.today():
            # Подписка истекла, обновляем статус
            cursor.execute(
                "UPDATE users SET premium_status = FALSE WHERE telegram_id = ?",
                (telegram_id,)
            )
            connection.commit()
            premium_status = False
    
    connection.close()
    return {
        "premium_status": bool(premium_status),
        "subscription_end_date": subscription_end,
        "auto_renewal": bool(auto_renewal)
    }

def activate_premium_subscription(telegram_id: int, days: int = None):
    """
    Активирует премиум подписку для пользователя.
    
    Args:
        telegram_id: ID пользователя в Telegram
        days: Количество дней подписки (по умолчанию из конфигурации)
    """
    if days is None:
        days = LimitsConfig.DEFAULT_SUBSCRIPTION_DAYS
    from datetime import date, timedelta
    
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    # Получаем текущую дату окончания подписки
    cursor.execute(
        "SELECT subscription_end_date FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )
    result = cursor.fetchone()
    
    if result and result[0]:
        # Если подписка уже есть, продлеваем её
        current_end = date.fromisoformat(result[0])
        if current_end > date.today():
            new_end = current_end + timedelta(days=days)
        else:
            new_end = date.today() + timedelta(days=days)
    else:
        # Новая подписка
        new_end = date.today() + timedelta(days=days)
    
    cursor.execute(
        "UPDATE users SET premium_status = TRUE, subscription_end_date = ?, subscription_type = ?, auto_renewal = TRUE WHERE telegram_id = ?",
        (new_end.isoformat(), days, telegram_id)
    )
    
    connection.commit()
    connection.close()

def get_all_premium_users() -> list:
    """
    Получает список всех активных премиум пользователей.
    
    Returns:
        Список словарей с информацией о премиум пользователях
    """
    from datetime import date
    
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    today = date.today().isoformat()
    
    cursor.execute(
        """
        SELECT telegram_id, username, subscription_end_date 
        FROM users 
        WHERE premium_status = TRUE 
        AND (subscription_end_date IS NULL OR subscription_end_date >= ?)
        """,
        (today,)
    )
    
    users = cursor.fetchall()
    connection.close()
    
    return [{
        'telegram_id': user[0],
        'username': user[1],
        'subscription_end': user[2]
    } for user in users]

def get_users_for_renewal_reminder():
    """
    Получает список пользователей с активным автопродлением, которым нужно отправить напоминание 
    о предстоящем автоматическом списании (за 3 дня до истечения подписки).
    
    Returns:
        Список пользователей для отправки напоминания
    """
    from datetime import date, timedelta
    
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    # Получаем пользователей с автопродлением, у которых подписка истекает через 3 дня
    reminder_date = date.today() + timedelta(days=3)
    
    cursor.execute(
        """
        SELECT telegram_id, username, subscription_end_date 
        FROM users 
        WHERE auto_renewal = TRUE 
        AND premium_status = TRUE
        AND subscription_end_date IS NOT NULL 
        AND subscription_end_date = ?
        """,
        (reminder_date.isoformat(),)
    )
    
    users = cursor.fetchall()
    connection.close()
    
    return [
        {
            'telegram_id': user[0],
            'username': user[1],
            'subscription_end_date': user[2]
        }
        for user in users
    ]

def set_auto_renewal(telegram_id: int, auto_renewal: bool):
    """
    Устанавливает статус автоматического продления подписки для пользователя.
    
    Args:
        telegram_id: ID пользователя в Telegram
        auto_renewal: Включить/выключить автоматическое продление
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    cursor.execute(
        "UPDATE users SET auto_renewal = ? WHERE telegram_id = ?",
        (auto_renewal, telegram_id)
    )
    
    connection.commit()
    connection.close()

def get_users_for_auto_renewal():
    """
    Получает список пользователей с активным автопродлением, у которых подписка истекает сегодня.
    
    Returns:
        Список пользователей для автоматического продления
    """
    from datetime import date
    
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    # Получаем пользователей с автопродлением, у которых подписка истекает сегодня
    today = date.today()
    
    cursor.execute(
        """
        SELECT telegram_id, username, subscription_end_date 
        FROM users 
        WHERE auto_renewal = TRUE 
        AND premium_status = TRUE
        AND subscription_end_date IS NOT NULL 
        AND subscription_end_date = ?
        """,
        (today.isoformat(),)
    )
    
    users = cursor.fetchall()
    connection.close()
    
    return [{
        'telegram_id': user[0],
        'username': user[1],
        'subscription_end': user[2]
    } for user in users]

def process_auto_renewal(telegram_id: int) -> bool:
    """
    Обрабатывает автоматическое продление подписки для пользователя.
    Использует сохраненный тип подписки для определения продолжительности.
    Автопродление теперь работает без списания звезд.
    
    Args:
        telegram_id: ID пользователя в Telegram
    
    Returns:
        True если продление успешно
    """
    from datetime import date, timedelta
    
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    # Получаем информацию о пользователе: тип подписки
    cursor.execute(
        "SELECT subscription_type FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )
    result = cursor.fetchone()
    
    if not result:
        connection.close()
        return False
    
    subscription_type = result[0]
    
    # Определяем продолжительность в зависимости от типа подписки
    if subscription_type == 1:
        days = 1
    elif subscription_type == 7:
        days = 7
    else:  # subscription_type == DEFAULT_SUBSCRIPTION_DAYS
        days = LimitsConfig.DEFAULT_SUBSCRIPTION_DAYS
    
    # Продлеваем подписку на соответствующий период
    new_end_date = date.today() + timedelta(days=days)
    
    cursor.execute(
        """
        UPDATE users 
        SET subscription_end_date = ?,
            premium_status = TRUE
        WHERE telegram_id = ?
        """,
        (new_end_date.isoformat(), telegram_id)
    )
    
    connection.commit()
    connection.close()
    return True

def update_user_preferences(telegram_id: int, use_emojis: bool = None, communication_style: str = None, preferred_response_length: str = None):
    """
    Обновляет пользовательские предпочтения.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    updates = []
    params = []
    
    if use_emojis is not None:
        updates.append("use_emojis = ?")
        params.append(use_emojis)
    
    if communication_style is not None:
        updates.append("communication_style = ?")
        params.append(communication_style)
    
    if preferred_response_length is not None:
        updates.append("preferred_response_length = ?")
        params.append(preferred_response_length)
    
    if updates:
        params.append(telegram_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE telegram_id = ?"
        cursor.execute(query, params)
        connection.commit()
    
    connection.close()

def get_user_preferences(telegram_id: int) -> dict:
    """
    Получает пользовательские предпочтения.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    cursor.execute(
        "SELECT use_emojis, communication_style, preferred_response_length FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )
    result = cursor.fetchone()
    connection.close()
    
    if result:
        return {
            'use_emojis': bool(result[0]) if result[0] is not None else True,
            'communication_style': result[1] or 'friendly',
            'preferred_response_length': result[2] or 'medium'
        }
    
    return {
        'use_emojis': True,
        'communication_style': 'friendly',
        'preferred_response_length': 'medium'
    }

if __name__ == "__main__":
    initialize_database()