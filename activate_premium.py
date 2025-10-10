import sys
import os
sys.path.append(os.path.dirname(os.path.abspath('.')))
from storage.db import activate_premium_subscription, get_user_premium_status, get_user_by_telegram_id
from datetime import datetime

telegram_id = 856108935

print(f'🔍 Поиск пользователя с ID: {telegram_id}')

try:
    # Получаем информацию о пользователе
    user = get_user_by_telegram_id(telegram_id)
    if user:
        username = user.get('username', 'Без имени')
        print(f'👤 Найден пользователь: {username} (ID: {telegram_id})')
        
        # Проверяем текущий статус премиума
        current_status = get_user_premium_status(telegram_id)
        is_premium_now = current_status.get('premium_status', False)
        status_text = "Премиум" if is_premium_now else "Обычный"
        print(f'📊 Текущий статус: {status_text}')
        
        # Активируем премиум на 30 дней
        print('🎯 Активирую премиум подписку на 30 дней...')
        activate_premium_subscription(telegram_id, days=30)
        
        # Проверяем новый статус
        new_status = get_user_premium_status(telegram_id)
        is_premium_new = new_status.get('premium_status', False)
        new_status_text = "Премиум" if is_premium_new else "Обычный"
        print(f'✅ Премиум активирован!')
        print(f'💎 Новый статус: {new_status_text}')
        
        premium_until = new_status.get('subscription_end_date')
        if premium_until:
            try:
                end_date = datetime.fromisoformat(premium_until.replace('Z', '+00:00')).strftime('%d.%m.%Y')
                print(f'📅 Действует до: {end_date}')
            except:
                print(f'📅 Действует до: {premium_until}')
        
        print(f'🎉 Пользователь {username} теперь имеет премиум подписку на месяц!')
        
    else:
        print(f'❌ Пользователь с ID {telegram_id} не найден в базе данных')
        
except Exception as e:
    print(f'❌ Ошибка при активации премиума: {e}')
    import traceback
    traceback.print_exc()