import sys
import os
sys.path.append(os.path.dirname(os.path.abspath('.')))
from storage.db import get_user_premium_status, get_user_by_telegram_id

telegram_id = 856108935

print(f'🔍 Проверка премиум статуса для пользователя ID: {telegram_id}')

try:
    # Получаем информацию о пользователе
    user = get_user_by_telegram_id(telegram_id)
    if user:
        username = user.get('username', 'Неизвестно')
        print(f'👤 Пользователь: {username}')
        
        # Проверяем премиум статус
        premium = get_user_premium_status(telegram_id)
        
        status_text = "✅ Активен" if premium["premium_status"] else "❌ Неактивен"
        print(f'👑 Премиум статус: {status_text}')
        
        subscription_end = premium["subscription_end_date"] or "Не активна"
        print(f'📅 Подписка до: {subscription_end}')
        
        auto_renewal_text = "✅ Включено" if premium["auto_renewal"] else "❌ Отключено"
        print(f'🔄 Автопродление: {auto_renewal_text}')
        
    else:
        print(f'❌ Пользователь с ID {telegram_id} не найден в базе данных')
        
except Exception as e:
    print(f'❌ Ошибка при проверке премиум статуса: {e}')
    import traceback
    traceback.print_exc()