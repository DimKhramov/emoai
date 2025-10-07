# Интеграция с Telegram через aiogram

import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from dotenv import load_dotenv
from services.intents import determine_intent
from services.journal import create_journal_entry
from services.microsteps import MICROSTEPS
from storage.db import (
    initialize_database, add_user, get_user_by_telegram_id, 
    is_new_user, add_message, get_conversation_history, 
    clear_conversation_history, get_user_stats,
    check_daily_message_limit, increment_daily_message_count, get_daily_message_count,
    get_user_premium_status, activate_premium_subscription
)
from services.gpt_service import chat_with_gpt
from payment_manager import create_star_invoice, process_successful_payment, get_user_payment_info, PaymentManager, send_premium_offer, send_premium_reminder, get_premium_stats

# Загрузка переменных окружения
load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")

if not API_TOKEN:
    raise ValueError("TELEGRAM_API_TOKEN не найден. Проверьте файл .env.")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Инициализируем базу данных при запуске
initialize_database()

def ensure_user_initialized(user_id: int, username: str = None, first_name: str = None):
    """Инициализация пользователя если он не существует"""
    if is_new_user(user_id):
        # Добавляем нового пользователя в базу данных
        add_user(username or first_name or f"user_{user_id}", user_id)
        return True  # Новый пользователь
    return False  # Существующий пользователь

# Функция save_user_data больше не нужна, данные сохраняются в БД автоматически

def load_user_data(user_id: int):
    """Загрузка данных пользователя из базы данных"""
    return get_user_by_telegram_id(user_id)

def add_to_conversation_history(user_id: int, role: str, content: str):
    """Добавление сообщения в историю разговора"""
    # Получаем внутренний ID пользователя из БД
    user = get_user_by_telegram_id(user_id)
    if user:
        add_message(user['id'], content, role)

@dp.message(Command('start'))
async def start_command(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Проверяем, новый ли это пользователь
    is_new = ensure_user_initialized(user_id, username, first_name)
    
    if is_new:
        welcome_text = f"👋 Привет, {first_name or 'друг'}!\n\n" \
                      "Я твой эмоциональный помощник. Расскажи мне, как дела, " \
                      "что у тебя на душе, и я постараюсь поддержать! 😊\n\n" \
                      "Используй /help чтобы узнать о доступных командах."
    else:
        welcome_text = f"👋 С возвращением, {first_name or 'друг'}!\n\n" \
                      "Рад снова тебя видеть! Как дела? 😊"
    
    await message.answer(welcome_text)

@dp.message(Command('help'))
async def help_command(message: Message):
    """Обработчик команды /help"""
    help_text = "🤖 Доступные команды:\n\n" \
               "• /start - Начать общение\n" \
               "• /help - Показать эту справку\n" \
               "• /stats - Показать статистику\n" \
               "• /clear - Очистить историю чата\n" \
               "• /premium - Информация о премиум подписке\n" \
               "• /balance - Проверить баланс звезд\n" \
               "• /test_reminder - Протестировать уведомления\n\n" \
               "💬 Общение с ботом:\n" \
               "Просто напиши мне что-нибудь, и я отвечу! 😊\n\n" \
               "🔔 Ежедневные напоминания: Каждый день в 10:00 я буду напоминать тебе о возможности пообщаться!\n\n" \
               "📝 Обратная связь:\n" \
               "Если что-то не работает или у вас есть предложения по улучшению бота, просто напишите мне об этом! " \
               "Я передам ваше сообщение разработчику. 🛠️"
    
    # Создаем клавиатуру с кнопкой "Назад"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    
    await message.answer(help_text, reply_markup=keyboard)

@dp.message(Command('stats'))
async def stats_command(message: Message):
    """Обработчик команды /stats"""
    user_id = message.from_user.id
    
    # Получаем данные пользователя из БД
    user = get_user_by_telegram_id(user_id)
    
    if user:
        stats = get_user_stats(user['id'])
        daily_count = get_daily_message_count(user_id)
        premium_info = get_user_premium_status(user_id)
        
        # Формируем текст статистики
        stats_text = f"📊 *Ваша статистика:*\n\n" \
                    f"• Сообщений отправлено: {stats['message_count']}\n"
        
        # Показываем лимит только для обычных пользователей
        if premium_info and premium_info['premium_status']:
            stats_text += f"• Сообщений сегодня: {daily_count} (безлимитно ⭐)\n"
        else:
            stats_text += f"• Сообщений сегодня: {daily_count}/10\n"
            
        stats_text += f"• Зарегистрирован: {user['created_at']}\n" \
                     f"• Последняя активность: {stats['last_activity'] or 'Неизвестно'}\n"
        
        # Добавляем информацию о премиум статусе
        if premium_info and premium_info['premium_status']:
            stats_text += f"\n⭐ Премиум статус: Активен\n" \
                         f"📅 Подписка до: {premium_info['subscription_end_date']}"
        else:
            stats_text += f"\n👑 Хотите премиум? Используйте /premium"
    else:
        stats_text = "📊 Статистика пока недоступна. Начни общение командой /start!"
    
    await message.answer(stats_text)

@dp.message(Command('clear'))
async def clear_command(message: Message):
    """Обработчик команды /clear"""
    user_id = message.from_user.id
    
    # Получаем данные пользователя из БД
    user = get_user_by_telegram_id(user_id)
    
    if user:
        clear_conversation_history(user['id'])
        await message.answer("🗑️ История чата очищена!")
    else:
        await message.answer("❌ Нет данных для очистки. Начни общение командой /start!")

@dp.message(Command('test_reminder'))
async def test_reminder_command(message: Message):
    """Обработчик команды /test_reminder - тестирование уведомлений"""
    user_id = message.from_user.id
    
    # Импортируем планировщик из app.py
    from app import scheduler
    
    if scheduler:
        success = await scheduler.send_test_reminder(user_id)
        if success:
            await message.reply("✅ Тестовое напоминание отправлено!")
        else:
            await message.reply("❌ Ошибка при отправке тестового напоминания.")
    else:
        await message.reply("⚠️ Планировщик не активен.")

@dp.message(Command('premium'))
async def premium_command(message: Message):
    """Обработчик команды /premium - информация о премиум подписке"""
    user_id = message.from_user.id
    
    # Получаем статус премиум пользователя
    premium_info = get_user_premium_status(user_id)
    
    if premium_info and premium_info['premium_status']:
        # Пользователь уже имеет премиум
        auto_renewal_status = "включено ✅" if premium_info.get('auto_renewal', False) else "отключено ❌"
        
        await message.answer(
            f"⭐ У вас активна премиум подписка!\n"
            f"📅 Подписка до: {premium_info['subscription_end_date']}\n"
            f"🔄 Автопродление: {auto_renewal_status}\n\n"
            f"🎯 Премиум преимущества:\n"
            f"• Безлимитные сообщения\n"
            f"• Приоритетная поддержка\n"
            f"• Расширенные функции\n\n"
            f"💡 Используйте кнопку ниже для управления подпиской:"
        )
        # Отправляем кнопки управления подпиской
        await send_premium_offer(bot, user_id)
    else:
        # Предлагаем купить премиум
        await send_premium_offer(bot, user_id)

@dp.message(Command('buy_premium'))
async def buy_premium_command(message: Message):
    """Обработчик команды /buy_premium - покупка премиум подписки"""
    user_id = message.from_user.id
    
    # Создаем инвойс для покупки премиум подписки (100 звезд на 30 дней)
    invoice = create_star_invoice(
        title="Премиум подписка",
        description="Премиум подписка на 30 дней - безлимитные сообщения и расширенные функции",
        payload=f"premium_30_{user_id}",
        star_count=100
    )
    
    await bot.send_invoice(
        chat_id=user_id,
        title=invoice['title'],
        description=invoice['description'],
        payload=invoice['payload'],
        provider_token="",  # Для Telegram Stars не нужен
        currency="XTR",  # Telegram Stars
        prices=[LabeledPrice(label="Премиум подписка", amount=invoice['star_count'])]
    )

@dp.message(Command('balance'))
async def balance_command(message: Message):
    """Обработчик команды /balance - проверка баланса звезд"""
    user_id = message.from_user.id
    
    payment_info = get_user_payment_info(user_id)
    
    if payment_info:
        await message.answer(
            f"💰 Ваш баланс:\n\n"
            f"👑 Премиум статус: {'Активен' if payment_info['premium_status'] else 'Неактивен'}\n"
            f"📅 Подписка до: {payment_info['subscription_end_date'] or 'Не активна'}"
        )
    else:
        await message.answer("❌ Информация о балансе недоступна. Начните с команды /start")

# Обработчики callback для кнопок премиума
@dp.callback_query(lambda c: c.data.startswith('buy_premium_'))
async def handle_premium_purchase(callback_query: CallbackQuery):
    """Обработчик покупки премиум подписки через кнопки"""
    user_id = callback_query.from_user.id
    plan = callback_query.data.split('_')[-1]  # daily, weekly, monthly
    
    # Определяем параметры плана
    plan_info = {
        'daily': {'days': 1, 'stars': 10, 'title': 'Премиум на день'},
        'weekly': {'days': 7, 'stars': 30, 'title': 'Премиум на неделю'},
        'monthly': {'days': 30, 'stars': 100, 'title': 'Премиум на месяц'}
    }
    
    if plan not in plan_info:
        await callback_query.answer("❌ Неверный план подписки")
        return
    
    info = plan_info[plan]
    
    # Создаем инвойс
    invoice = create_star_invoice(
        title=info['title'],
        description=f"Премиум подписка на {info['days']} дн. - безлимитные сообщения и расширенные функции",
        payload=f"premium_{info['days']}_{user_id}",
        star_count=info['stars']
    )
    
    try:
        await bot.send_invoice(
            chat_id=user_id,
            title=invoice['title'],
            description=invoice['description'],
            payload=invoice['payload'],
            provider_token="",  # Для Telegram Stars не нужен
            currency="XTR",  # Telegram Stars
            prices=[LabeledPrice(label=info['title'], amount=invoice['star_count'])]
        )
        await callback_query.answer("💫 Инвойс отправлен!")
    except Exception as e:
        await callback_query.answer("❌ Ошибка при создании инвойса")
        print(f"Ошибка создания инвойса: {e}")

@dp.callback_query(lambda c: c.data == 'check_balance')
async def handle_check_balance(callback_query: CallbackQuery):
    """Обработчик проверки баланса через кнопку"""
    user_id = callback_query.from_user.id
    
    payment_info = get_user_payment_info(user_id)
    
    if payment_info:
        balance_text = (
            f"💰 Ваш баланс:\n\n"
            f"👑 Премиум статус: {'✅ Активен' if payment_info['premium_status'] else '❌ Неактивен'}\n"
            f"📅 Подписка до: {payment_info['subscription_end_date'] or 'Не активна'}"
        )
        
        # Создаем клавиатуру с кнопкой "Назад"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ])
        
        await callback_query.message.edit_text(balance_text, reply_markup=keyboard)
        await callback_query.answer("💰 Баланс обновлен")
    else:
        await callback_query.answer("❌ Информация о балансе недоступна")

@dp.callback_query(lambda c: c.data == 'toggle_auto_renewal')
async def handle_toggle_auto_renewal(callback_query: CallbackQuery):
    """Обработчик переключения автопродления подписки"""
    user_id = callback_query.from_user.id
    
    # Получаем текущий статус автопродления
    user_info = get_user_payment_info(user_id)
    if not user_info:
        await callback_query.answer("❌ Информация о пользователе недоступна")
        return
    
    current_auto_renewal = user_info.get('auto_renewal', False)
    new_auto_renewal = not current_auto_renewal
    
    # Создаем экземпляр PaymentManager и переключаем автопродление
    payment_manager = PaymentManager()
    success = await payment_manager.toggle_auto_renewal(user_id, new_auto_renewal)
    
    if success:
        status_text = "включено ✅" if new_auto_renewal else "отключено ❌"
        await callback_query.answer(f"🔄 Автопродление {status_text}")
        
        # Обновляем сообщение с новым статусом
        await send_premium_offer(bot, user_id)
        await callback_query.message.delete()
    else:
        await callback_query.answer("❌ Ошибка при изменении настроек автопродления")

@dp.callback_query(lambda c: c.data == 'back_to_main')
async def handle_back_to_main(callback_query: CallbackQuery):
    """Обработчик кнопки 'Назад' - возврат к главному меню"""
    user_id = callback_query.from_user.id
    
    # Удаляем текущее сообщение с кнопками
    await callback_query.message.delete()
    
    # Отправляем приветственное сообщение
    welcome_text = (
        "👋 Добро пожаловать в Эмо-друг!\n\n"
        "🤖 Я ваш персональный помощник для эмоциональной поддержки.\n"
        "💬 Просто напишите мне о своих переживаниях, и я помогу вам разобраться в них.\n\n"
        "📋 Доступные команды:\n"
        "• /premium - информация о премиум подписке\n"
        "• /help - помощь и инструкции\n\n"
        "✨ Начните общение, написав мне что-нибудь!"
    )
    
    await callback_query.message.answer(welcome_text)
    await callback_query.answer("🔙 Возврат в главное меню")

@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    """Обработчик предварительной проверки платежа"""
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(lambda message: message.successful_payment)
async def successful_payment_handler(message: Message):
    """Обработчик успешного платежа"""
    user_id = message.from_user.id
    payment = message.successful_payment
    
    # Определяем количество дней по сумме платежа
    total_amount = payment.total_amount
    days = 30  # По умолчанию месяц
    if total_amount == 10:
        days = 1
    elif total_amount == 30:
        days = 7
    elif total_amount == 100:
        days = 30
    
    # Обрабатываем успешный платеж
    success = process_successful_payment(user_id, payment.telegram_payment_charge_id, total_amount)
    
    if success:
        # Активируем подписку с правильным типом
        # activate_premium_subscription теперь сохраняет тип подписки для автопродления
        activate_premium_subscription(user_id, days)
        
        # Формируем правильное сообщение в зависимости от количества дней
        if days == 1:
            period_text = "1 день"
        elif days == 7:
            period_text = "7 дней"
        else:
            period_text = "30 дней"
            
        await message.answer(
            f"🎉 Платеж успешно обработан!\n\n"
            f"⭐ Премиум подписка активирована на {period_text}\n"
            f"🚀 Теперь у вас безлимитные сообщения!\n\n"
            f"Используйте /premium для просмотра статуса подписки"
        )
    else:
        await message.answer(
            "❌ Произошла ошибка при обработке платежа.\n"
            "Обратитесь в поддержку для решения проблемы."
        )

async def get_gpt_response(user_id: int, user_message: str) -> str:
    """Получение ответа от GPT с историей разговора"""
    user = get_user_by_telegram_id(user_id)
    conversation_history = get_conversation_history(user['id']) if user else []
    gpt_history = [{'role': msg['role'], 'content': msg['content']} for msg in conversation_history]
    return await chat_with_gpt(user_message, conversation_history=gpt_history)

async def send_typing_action(chat_id: int):
    """Отправляет действие 'печатает' в чат"""
    try:
        await bot.send_chat_action(chat_id=chat_id, action="typing")
    except Exception as e:
        print(f"Ошибка при отправке typing action: {e}")

async def handle_talk_intent(message: Message, user_id: int, user_message: str):
    """Обработка интента talk"""
    # Показываем что бот печатает
    await send_typing_action(message.chat.id)
    
    response = await get_gpt_response(user_id, user_message)
    if not response:
        response = "Привет! Как ты себя чувствуешь? 😊 Расскажи мне что у тебя на душе!"
    await message.reply(response)
    add_to_conversation_history(user_id, 'assistant', response)

async def handle_other_intent(message: Message, user_id: int, user_message: str):
    """Обработка неопознанных интентов"""
    # Показываем что бот печатает
    await send_typing_action(message.chat.id)
    
    response = await get_gpt_response(user_id, user_message)
    if not response:
        response = "Я здесь, чтобы помочь! Расскажи, что у тебя на уме. 🤗"
    await message.reply(response)
    add_to_conversation_history(user_id, 'assistant', response)

async def handle_simple_intent(message: Message, user_id: int, intent: str):
    """Обработка простых интентов с предопределенными ответами"""
    # Показываем что бот печатает
    await send_typing_action(message.chat.id)
    
    responses = {
        "coach": "Понимаю, что тебе нужна поддержка. Расскажи подробнее, что происходит? 🤗",
        "facts": "Вот несколько шагов, которые могут помочь:\n\n" + "\n".join([f"• {step}" for step in MICROSTEPS[:3]]),
        "journal": "Давай запишем дневник! 📔\n\nКакое у тебя настроение от 0 до 10? И расскажи, что происходило сегодня?",
        "sos": """🆘 Ты не один, я рядом! 

Если нужна срочная помощь:
📞 Телефон доверия: 8-800-2000-122
🚑 Экстренные службы: 112

А пока расскажи мне, что происходит? Я выслушаю и поддержу! 💙"""
    }
    
    response = responses.get(intent, "Я здесь, чтобы помочь! 🤗")
    await message.reply(response)
    add_to_conversation_history(user_id, 'assistant', response)

@dp.message()
async def handle_message(message: Message):
    """Основной обработчик сообщений"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    user_message = message.text
    
    if not user_message:
        await message.reply("Пожалуйста, отправьте текстовое сообщение 📝")
        return
    
    # Инициализируем пользователя если он новый
    is_new = ensure_user_initialized(user_id, username, first_name)
    
    if is_new:
        welcome_message = (
            "👋 Привет! Я твой эмоциональный друг-бот.\n\n"
            "Я могу:\n"
            "• 💬 Поговорить с тобой на любые темы\n"
            "• 🎯 Дать совет как коуч\n"
            "• 📚 Поделиться интересными фактами\n"
            "• 📝 Помочь с ведением дневника\n"
            "• 🆘 Поддержать в трудную минуту\n\n"
            "Просто напиши мне что-нибудь! 😊\n\n"
            "📊 /stats - твоя статистика\n"
            "🗑️ /clear - очистить историю чата\n"
            "⭐ /premium - премиум подписка"
        )
        await message.reply(welcome_message)
        return
    
    # Проверяем премиум статус пользователя
    premium_info = get_user_premium_status(user_id)
    is_premium = premium_info and premium_info['premium_status']
    
    # Проверяем лимит сообщений только для обычных пользователей
    if not is_premium and not check_daily_message_limit(user_id):
        limit_message = (
            f"🚫 Вы достигли дневного лимита сообщений (10/10).\n\n"
            f"💡 Хотите безлимитные сообщения?\n"
            f"⭐ Оформите премиум подписку: /premium\n\n"
            f"Или попробуйте снова завтра! 😊"
        )
        await message.reply(limit_message)
        return
    
    # Увеличиваем счетчик сообщений только для обычных пользователей
    if not is_premium:
        increment_daily_message_count(user_id)
    
    # Добавляем сообщение пользователя в историю
    add_to_conversation_history(user_id, 'user', user_message)
    
    # Определяем интент пользователя
    intent = determine_intent(user_message)
    
    try:
        if intent == "talk":
            await handle_talk_intent(message, user_id, user_message)
        elif intent in ["coach", "facts", "journal", "sos"]:
            await handle_simple_intent(message, user_id, intent)
        else:
            await handle_other_intent(message, user_id, user_message)
            
    except Exception as e:
        print(f"Ошибка при обработке сообщения: {e}")
        error_response = "Извини, произошла ошибка. Попробуй еще раз! 😅"
        await message.reply(error_response)
        add_to_conversation_history(user_id, 'assistant', error_response)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())