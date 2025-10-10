# Интеграция с Telegram через aiogram

import os
import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LimitsConfig, PremiumConfig, SchedulerConfig, OpenAIConfig
from services.intents import determine_intent
from services.microsteps import MICROSTEPS
from storage.db import (
    initialize_database, add_user, get_user_by_telegram_id, 
    is_new_user, add_message, get_conversation_history, 
    clear_conversation_history, get_user_stats,
    check_daily_message_limit, increment_daily_message_count, get_daily_message_count,
    get_user_premium_status, activate_premium_subscription
)
from services.gpt_service import (
    chat_with_gpt, detect_emotion_keywords, get_openai_client
)
from payment_manager import create_star_invoice, process_successful_payment, get_user_payment_info, PaymentManager, send_premium_offer, send_premium_reminder, get_premium_stats
from handlers.preferences import router as preferences_router

# Загрузка переменных окружения
load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")

if not API_TOKEN:
    raise ValueError("TELEGRAM_API_TOKEN не найден. Проверьте файл .env.")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Регистрация роутеров
dp.include_router(preferences_router)

# Инициализация базы данных
initialize_database()

# Константы для простых интентов
SIMPLE_INTENT_TEXTS = {
    'greeting': "👋 Привет! Как дела? Расскажи, что у тебя на душе!",
    'goodbye': "👋 До свидания! Было приятно пообщаться. Возвращайся, когда захочешь поговорить!",
    'gratitude': "😊 Пожалуйста! Я всегда рад помочь. Если что-то еще понадобится - обращайся!",
    'compliment': "😊 Спасибо за добрые слова! Мне тоже приятно с тобой общаться!",
    'weather': "🌤️ К сожалению, я не могу проверить погоду, но могу поговорить о том, как погода влияет на настроение!",
    'time': "⏰ Я не знаю точного времени, но могу помочь с планированием дня или поговорить о времени в философском смысле!"
}

# Добавляем дополнительные константы для простых интентов
ADDITIONAL_INTENT_TEXTS = {
    "coach": "Понимаю, что тебе нужна поддержка. Расскажи подробнее, что происходит? 🤗",
    "facts": "Вот несколько шагов, которые могут помочь:\n\n" + "\n".join([f"• {step}" for step in MICROSTEPS[:3]]),
    "journal": "Давай запишем дневник! 📔\n\nКакое у тебя настроение от 0 до 10? И расскажи, что происходило сегодня?",
    "sos": """🆘 Ты не один, я рядом! 

Если нужна срочная помощь:
📞 Телефон доверия: 8-800-2000-122
🚑 Экстренные службы: 112

А пока расскажи мне, что происходит? Я выслушаю и поддержу! 💙"""
}

# Вспомогательные функции
def render_welcome(is_new: bool, first_name: str | None) -> str:
    """Генерирует приветственное сообщение в зависимости от статуса пользователя"""
    name = first_name or 'друг'
    
    if is_new:
        return (
            f"👋 Привет, {name}!\n\n"
            "Я твой эмоциональный помощник. Расскажи мне, как дела, "
            "что у тебя на душе, и я постараюсь поддержать! 😊\n\n"
            "Используй /help чтобы узнать о доступных командах."
        )
    else:
        return (
            f"👋 С возвращением, {name}!\n\n"
            "Рад снова тебя видеть! Как дела? 😊"
        )

def render_welcome_detailed(first_name: str | None) -> str:
    """Генерирует подробное приветственное сообщение для новых пользователей в handle_message"""
    return (
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

def format_premium_line(premium_info) -> str:
    """Форматирует строку с информацией о премиум статусе"""
    if premium_info and premium_info['premium_status']:
        return f"👑 Премиум статус: {'✅ Активен' if premium_info['premium_status'] else '❌ Неактивен'}\n📅 Подписка до: {premium_info['subscription_end_date']}"
    else:
        return "👑 Премиум статус: ❌ Неактивен\n📅 Подписка до: Не активна"

def render_premium_status_text(premium_info) -> str:
    """Генерирует текст статуса премиум подписки"""
    if premium_info and premium_info['premium_status']:
        auto_renewal_status = "включено ✅" if premium_info.get('auto_renewal', False) else "отключено ❌"
        return (
            f"⭐ У вас активна премиум подписка!\n"
            f"📅 Подписка до: {premium_info['subscription_end_date']}\n"
            f"🔄 Автопродление: {auto_renewal_status}\n\n"
            f"🎯 Премиум преимущества:\n"
            f"• Безлимитные сообщения\n"
            f"• Приоритетная поддержка\n"
            f"• Расширенные функции\n\n"
            f"💡 Используйте кнопку ниже для управления подпиской:"
        )
    else:
        return "Информация о премиум подписке будет отображена через кнопки ниже."

def kb_back_to_main() -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопкой 'Назад'"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])

async def safe_delete(message: Message) -> bool:
    """Безопасно удаляет сообщение с обработкой ошибок"""
    try:
        await message.delete()
        return True
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
        return False

async def check_and_increment_daily_limit(user_id: int, message: Message) -> bool:
    """Проверяет и увеличивает дневной лимит сообщений"""
    # Сначала проверяем премиум статус
    premium_info = get_user_premium_status(user_id)
    if premium_info and premium_info['premium_status']:
        # Премиум пользователи имеют безлимитный доступ, не увеличиваем счетчик
        return True
    
    if not check_daily_message_limit(user_id):
        # Простое сообщение о лимите
        limit_message = "Похоже, ты достиг(ла) дневного лимита сообщений (20/20). Можем продолжить завтра или оформить премиум — как тебе удобнее?"
        
        # Создаем кнопки для покупки премиума
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💎 Купить премиум", callback_data="buy_premium_monthly")],
            [InlineKeyboardButton(text="📊 Проверить баланс", callback_data="check_balance")]
        ])
        
        # Добавляем эмодзи
        full_message = f"💪 {limit_message}"
        
        await message.answer(full_message, reply_markup=keyboard)
        return False
    
    # Увеличиваем счетчик только для обычных пользователей
    increment_daily_message_count(user_id)
    return True

async def send_premium_invoice(user_id: int, days: int, price: int, title: str, description: str) -> bool:
    """Отправляет инвойс для покупки премиум подписки"""
    try:
        invoice = create_star_invoice(
            title=title,
            description=description,
            payload=f"premium_{days}_{user_id}",
            star_count=price
        )
        
        await bot.send_invoice(
            chat_id=user_id,
            title=invoice['title'],
            description=invoice['description'],
            payload=invoice['payload'],
            provider_token="",  # Для Telegram Stars не нужен
            currency="XTR",  # Telegram Stars
            prices=[LabeledPrice(label=title, amount=invoice['star_count'])]
        )
        return True
    except Exception as e:
        print(f"Ошибка создания инвойса: {e}")
        return False

async def reply_with_text_and_log(message: Message, user_id: int, text: str):
    """Отправляет ответ и логирует в историю разговора"""
    await message.reply(text)
    add_to_conversation_history(user_id, "assistant", text)

async def reply_with_gpt(message: Message, user_id: int, user_message: str, fallback_text: str):
    """Обрабатывает GPT ответ с typing action и логированием"""
    await send_typing_action(message.chat.id)
    
    gpt_response = await get_gpt_response(user_id, user_message)
    if not gpt_response:
        gpt_response = fallback_text
    
    await message.reply(gpt_response)
    add_to_conversation_history(user_id, "assistant", gpt_response)

def ensure_user_initialized(user_id: int, username: str = None, first_name: str = None):
    """Инициализация пользователя если он не существует"""
    if is_new_user(user_id):
        # Добавляем нового пользователя в базу данных
        result = add_user(username or first_name or f"user_{user_id}", user_id)
        if result > 0:
            return True  # Новый пользователь успешно добавлен
        else:
            print(f"Ошибка при добавлении пользователя {user_id}")
            return False  # Ошибка при добавлении
    return False  # Существующий пользователь

# Функция save_user_data больше не нужна, данные сохраняются в БД автоматически

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
    
    # Формируем приветственное сообщение
    welcome_text = render_welcome(is_new, first_name)
    
    await message.answer(welcome_text)

@dp.message(Command('help'))
async def help_command(message: Message):
    """Обработчик команды /help"""
    help_text = f"🤖 Доступные команды:\n\n" \
               f"• /start - Начать общение\n" \
               f"• /help - Показать эту справку\n" \
               f"• /settings - Настройки общения\n" \
               f"• /stats - Показать статистику\n" \
               f"• /clear - Очистить историю чата\n" \
               f"• /premium - Информация о премиум подписке\n" \
               f"• /balance - Проверить баланс звезд\n" \
               f"• /test_reminder - Протестировать уведомления\n\n" \
               f"💬 Общение с ботом:\n" \
               f"Просто напиши мне что-нибудь, и я отвечу! 😊\n\n" \
               f"🔔 Ежедневные напоминания: Каждый день в {SchedulerConfig.DAILY_REMINDER_TIME.strftime('%H:%M')} я буду напоминать тебе о возможности пообщаться!\n\n" \
               f"📝 Обратная связь:\n" \
               f"Если что-то не работает или у вас есть предложения по улучшению бота, просто напишите мне об этом! " \
               f"Я передам ваше сообщение разработчику. 🛠️"
    
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
            stats_text += f"• Сообщений сегодня: {daily_count}/{LimitsConfig.DAILY_MESSAGE_LIMIT}\n"
            
        stats_text += f"• Зарегистрирован: {user['created_at']}\n" \
                     f"• Последняя активность: {stats['last_activity'] or 'Неизвестно'}\n"
        
        # Добавляем информацию о премиум статусе
        premium_line = format_premium_line(premium_info)
        stats_text += f"\n{premium_line}"
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
        status_text = render_premium_status_text(premium_info)
        await message.answer(status_text)
    
    # Отправляем кнопки управления подпиской (для всех пользователей)
    await send_premium_offer(bot, user_id)

@dp.message(Command('buy_premium'))
async def buy_premium_command(message: Message):
    """Обработчик команды /buy_premium - покупка премиум подписки"""
    user_id = message.from_user.id
    
    # Отправляем инвойс для месячной подписки
    success = await send_premium_invoice(
        user_id=user_id,
        days=PremiumConfig.MONTHLY_DAYS,
        price=PremiumConfig.MONTHLY_PRICE,
        title="Премиум подписка",
        description=f"Премиум подписка на {PremiumConfig.MONTHLY_DAYS} дней - безлимитные сообщения и расширенные функции"
    )
    
    if not success:
        await message.reply("❌ Ошибка при создании инвойса. Попробуйте позже.")

@dp.message(Command('balance'))
async def balance_command(message: Message):
    """Обработчик команды /balance - проверка баланса звезд"""
    user_id = message.from_user.id
    
    payment_info = get_user_payment_info(user_id)
    
    if payment_info:
        premium_line = format_premium_line(payment_info)
        await message.answer(f"💰 Ваш баланс:\n\n{premium_line}")
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
        'daily': {'days': PremiumConfig.DAILY_DAYS, 'stars': PremiumConfig.DAILY_PRICE, 'title': 'Премиум на день'},
        'weekly': {'days': PremiumConfig.WEEKLY_DAYS, 'stars': PremiumConfig.WEEKLY_PRICE, 'title': 'Премиум на неделю'},
        'monthly': {'days': PremiumConfig.MONTHLY_DAYS, 'stars': PremiumConfig.MONTHLY_PRICE, 'title': 'Премиум на месяц'}
    }
    
    if plan not in plan_info:
        await callback_query.answer("❌ Неверный план подписки")
        return
    
    info = plan_info[plan]
    
    # Отправляем инвойс
    success = await send_premium_invoice(
        user_id=user_id,
        days=info['days'],
        price=info['stars'],
        title=info['title'],
        description=f"Премиум подписка на {info['days']} дн. - безлимитные сообщения и расширенные функции"
    )
    
    if success:
        await callback_query.answer("💫 Инвойс отправлен!")
    else:
        await callback_query.answer("❌ Ошибка при создании инвойса")

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
    first_name = callback_query.from_user.first_name
    
    # Удаляем текущее сообщение с кнопками
    await safe_delete(callback_query.message)
    
    # Отправляем приветственное сообщение
    welcome_text = render_welcome(is_new=False, first_name=first_name)
    
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
    days = LimitsConfig.DEFAULT_SUBSCRIPTION_DAYS  # По умолчанию
    if total_amount == PremiumConfig.DAILY_PRICE:
        days = PremiumConfig.DAILY_DAYS
    elif total_amount == PremiumConfig.WEEKLY_PRICE:
        days = PremiumConfig.WEEKLY_DAYS
    elif total_amount == PremiumConfig.MONTHLY_PRICE:
        days = PremiumConfig.MONTHLY_DAYS
    
    # Обрабатываем успешный платеж
    success = process_successful_payment(user_id, payment.telegram_payment_charge_id, total_amount)
    
    if success:
        # Активируем подписку с правильным типом
        # activate_premium_subscription теперь сохраняет тип подписки для автопродления
        activate_premium_subscription(user_id, days)
        
        # Формируем правильное сообщение в зависимости от количества дней
        if days == PremiumConfig.DAILY_DAYS:
            period_text = f"{PremiumConfig.DAILY_DAYS} день"
        elif days == PremiumConfig.WEEKLY_DAYS:
            period_text = f"{PremiumConfig.WEEKLY_DAYS} дней"
        else:
            period_text = f"{PremiumConfig.MONTHLY_DAYS} дней"
            
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
    """Обрабатывает интент 'talk' - эмоциональная поддержка"""
    await send_typing_action(message.chat.id)
    
    # Определяем эмоциональное состояние
    emotion_type = detect_emotion_keywords(user_message)
    
    if emotion_type == "sos":
        # Критическая ситуация - специальная обработка
        response = """🆘 Ты не один, я рядом! 💛

Если есть угроза жизни — позвони в экстренные службы прямо сейчас.
Свяжись с близким человеком, который может быть рядом.

Давай сделаем 5 медленных вдохов: вдох на 4, выдох на 6. 🤍

Ты сейчас в безопасности?"""
        
        await reply_with_text_and_log(message, user_id, response)
        return
    
    elif emotion_type == "neutral":
        # Для нейтральных сообщений используем GPT для релевантного ответа
        try:
            client = get_openai_client()
            
            prompt = f"""Ты дружелюбный помощник. Пользователь написал нейтральное сообщение: "{user_message}"

Дай короткий (1-2 предложения), дружелюбный и релевантный ответ на русском языке. 
Отвечай по существу вопроса, будь естественным и добрым. Можешь использовать 1-2 эмодзи.

Ответ:"""

            response = client.chat.completions.create(
                model=OpenAIConfig.MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=OpenAIConfig.MAX_TOKENS,
                temperature=OpenAIConfig.TEMPERATURE
            )
            
            gpt_response = response.choices[0].message.content.strip()
            await reply_with_text_and_log(message, user_id, gpt_response)
            return
            
        except Exception as e:
            print(f"Ошибка при генерации ответа для нейтрального сообщения: {e}")
            # Fallback к простым ответам
            neutral_responses = [
                "Понимаю! 😊 Расскажи больше?",
                "Интересно! 🤔 Что думаешь об этом?",
                "Хорошо! 👍 Как дела вообще?",
                "Ясно! 😌 А что еще происходит?"
            ]
            response = random.choice(neutral_responses)
            await reply_with_text_and_log(message, user_id, response)
            return
    
    # Для эмоциональных сообщений
    if emotion_type == "anger":
        opener = "Похоже, тебя это реально взбесило 😤"
        followup = "Что именно бесит сильнее всего?"
    elif emotion_type == "sadness":
        opener = "Звучит, будто тебе грустно 😞"
        followup = "О чём сейчас больше всего тоска?"
    elif emotion_type == "tired":
        opener = "Кажется, просто всё достало 😩"
        followup = "Где основная утечка сил?"
    elif emotion_type == "generic":
        # Для generic сообщений используем более нейтральный подход
        try:
            client = get_openai_client()
            
            prompt = f"""Пользователь написал: "{user_message}"

Дай короткий (1-2 предложения), дружелюбный и релевантный ответ на русском языке. 
Отвечай по существу, будь естественным и добрым. Можешь использовать 1-2 эмодзи.
Не предполагай эмоциональных проблем, если они не очевидны.

Ответ:"""

            response = client.chat.completions.create(
                model=OpenAIConfig.MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=OpenAIConfig.MAX_TOKENS,
                temperature=OpenAIConfig.TEMPERATURE
            )
            
            gpt_response = response.choices[0].message.content.strip()
            await reply_with_text_and_log(message, user_id, gpt_response)
            return
            
        except Exception as e:
            print(f"Ошибка при генерации ответа для generic сообщения: {e}")
            # Fallback к простым ответам
            generic_responses = [
                "Понимаю! 😊 Расскажи больше?",
                "Интересно! 🤔 Что думаешь об этом?",
                "Хорошо! 👍 Как дела вообще?",
                "Ясно! 😌 А что еще происходит?"
            ]
            response = random.choice(generic_responses)
            await reply_with_text_and_log(message, user_id, response)
            return
    else:
        # Только для явно эмоциональных состояний (anger, sadness, tired)
        opener = "Похоже, тебе сейчас непросто 😔"
        followup = "Хочешь рассказать, что случилось?"
    
    # Простые микро-шаги
    micro_steps = [
        "Сделай 3 глубоких вдоха и медленные выдохи",
        "Выпей стакан воды маленькими глотками", 
        "Выйди на 5 минут на воздух или к окну",
        "Потянись: плечи назад, шея — мягко, 30 секунд"
    ]
    micro_step = random.choice(micro_steps)
    
    # Простые завершающие фразы
    closers = ["Хочешь рассказать ещё немного?", "Ок?", "Что чувствуешь сейчас?"]
    closer = random.choice(closers)
    
    response = f"""{opener}

{followup}

👉 **{micro_step}**

{closer} 💛"""
    
    await reply_with_text_and_log(message, user_id, response)

async def handle_other_intent(message: Message, user_id: int, user_message: str):
    """Обрабатывает другие интенты (coach, facts, journal)"""
    intent = determine_intent(user_message)
    
    if intent == "coach":
        response = """💪 Понимаю, что тебе нужна поддержка!

Давай разберём по шагам:
• Сформулируй проблему в одном предложении
• Определи, что в твоём контроле и что вне его
• Выбери 1 шаг на 5–10 минут — сделай его и вернись

Расскажи подробнее, что происходит? 🤗"""
        
    elif intent == "facts":
        response = """📘 Коротко по делу:

• Сделай 3 глубоких вдоха и медленные выдохи
• Выпей стакан воды маленькими глотками
• Выйди на 5 минут на воздух или к окну

Что конкретно тебя беспокоит?"""
        
    elif intent == "journal":
        response = """📓 Давай запишем дневник! 💭

• Оцени настроение от 0 до 10
• Что сегодня произошло? 2–3 короткие факта
• За что благодарен(на) сегодня? (1 строка)
• Один простой план на завтра

Начни с любого пункта! 🌿"""
        
    else:
        # Fallback
        response = await get_gpt_response(user_id, user_message)
    
    await reply_with_text_and_log(message, user_id, response)

async def handle_unified_message(message: Message, user_id: int, user_message: str):
    """Единый упрощенный обработчик всех сообщений через GPT с эмоциональным контекстом"""
    await send_typing_action(message.chat.id)
    
    # Проверяем контент на неподходящие темы
    from services.content_filter import ContentFilter
    is_inappropriate, topic_type, safe_response = ContentFilter.check_content(user_message)
    
    if is_inappropriate:
        print(f"Заблокирован неподходящий контент: {topic_type} от пользователя {user_id}")
        await reply_with_text_and_log(message, user_id, safe_response)
        return
    
    # Получаем пользовательские предпочтения
    from storage.db import get_user_preferences
    user_preferences = get_user_preferences(message.from_user.id)
    
    # Получаем историю разговора для контекста
    from config import LimitsConfig
    from services.emotional_context import format_context_for_gpt
    
    context_limit = LimitsConfig.CONTEXT_MESSAGE_LIMIT
    history = get_conversation_history(user_id, limit=context_limit)
    
    # Анализируем эмоциональный контекст
    context_analysis, intent, response_tone, context_addition = format_context_for_gpt(history, user_message)
    
    # Формируем контекст для GPT
    context_messages = []
    for msg in history[-context_limit:]:  # Последние N сообщений согласно конфигурации
        role = "user" if msg['role'] == 'user' else "assistant"
        context_messages.append({"role": role, "content": msg['content']})
    
    # Добавляем текущее сообщение
    context_messages.append({"role": "user", "content": user_message})
    
    try:
        # Получаем ответ от GPT с полным контекстом, эмоциональным анализом и пользовательскими предпочтениями
        response = await get_gpt_response_with_context(context_messages, intent, response_tone, context_addition, user_preferences)
        await reply_with_text_and_log(message, user_id, response)
    except Exception as e:
        print(f"Ошибка при получении ответа от GPT: {e}")
        # Fallback ответы с учетом эмоционального состояния и предпочтений пользователя
        emotional_state = context_analysis.get('emotional_state', 'neutral')
        
        # Учитываем предпочтения пользователя в fallback ответах
        emoji_suffix = "" if not user_preferences.get('use_emojis', True) else " 💙"
        
        if emotional_state == 'negative':
            fallback_responses = [
                f"Понимаю, тебе сейчас непросто...{emoji_suffix}",
                f"Я здесь, чтобы выслушать тебя{emoji_suffix}",
                f"Чувствую, что тебе тяжело. Хочешь поговорить об этом?{emoji_suffix}"
            ]
        elif emotional_state == 'positive':
            fallback_responses = [
                f"Здорово! Расскажи больше!{emoji_suffix}",
                f"Классно! Что тебя так радует?{emoji_suffix}",
                f"Отлично! Поделись подробностями!{emoji_suffix}"
            ]
        else:
            fallback_responses = [
                f"Понимаю тебя! Расскажи больше?{emoji_suffix}",
                f"Интересно! Что думаешь об этом?{emoji_suffix}",
                f"Я здесь, чтобы выслушать тебя{emoji_suffix}"
            ]
        response = random.choice(fallback_responses)
        await reply_with_text_and_log(message, user_id, response)

async def get_gpt_response_with_context(context_messages, intent=None, response_tone=None, context_addition="", user_preferences=None):
    """Получение ответа от GPT с учетом контекста разговора и эмоционального анализа"""
    client = get_openai_client()
    
    # Выбираем подходящий промпт в зависимости от интента
    if intent in ['support', 'sos', 'emotional']:
        prompt_file = 'prompts/empathic_prompt.txt'
    elif intent in ['question', 'facts', 'advice', 'weather', 'time']:
        prompt_file = 'prompts/factual_prompt.txt'
    else:
        prompt_file = 'prompts/system_prompt.txt'
    
    # Читаем выбранный промпт
    with open(prompt_file, 'r', encoding='utf-8') as f:
        system_prompt = f.read()
    
    # Добавляем пользовательские предпочтения к промпту
    if user_preferences:
        preferences_text = ""
        if not user_preferences.get('use_emojis', True):
            preferences_text += "\n⚠️ ВАЖНО: Пользователь просил НЕ ИСПОЛЬЗОВАТЬ эмодзи в ответах."
        
        style = user_preferences.get('communication_style', 'friendly')
        if style == 'formal':
            preferences_text += "\n📝 Стиль общения: формальный, вежливый, без сленга."
        elif style == 'casual':
            preferences_text += "\n😎 Стиль общения: неформальный, дружеский, можно использовать сленг."
        
        length = user_preferences.get('preferred_response_length', 'medium')
        if length == 'short':
            preferences_text += "\n📏 Длина ответов: краткие (1-2 предложения)."
        elif length == 'long':
            preferences_text += "\n📖 Длина ответов: подробные (можно больше 4 предложений)."
        
        if preferences_text:
            system_prompt += preferences_text
    
    # Добавляем контекстную информацию к системному промпту
    if context_addition:
        system_prompt += f"\n\n{context_addition}"
    
    # Добавляем информацию о тоне ответа
    if response_tone:
        system_prompt += f"\n\nТон ответа: {response_tone}"
    
    # Добавляем информацию об интенте
    if intent:
        system_prompt += f"\n\nТип сообщения пользователя: {intent}"
    
    # Формируем сообщения для GPT
    messages = [{"role": "system", "content": system_prompt}] + context_messages
    
    response = client.chat.completions.create(
        model=OpenAIConfig.MODEL,
        messages=messages,
        max_tokens=OpenAIConfig.MAX_TOKENS,
        temperature=OpenAIConfig.TEMPERATURE
    )
    
    return response.choices[0].message.content.strip()

async def handle_simple_intent(message: Message, user_id: int, intent: str):
    """Обработка простых интентов"""
    # Показываем что бот печатает
    await send_typing_action(message.chat.id)
    
    # Для остальных интентов используем стандартные тексты
    all_intent_texts = {**SIMPLE_INTENT_TEXTS, **ADDITIONAL_INTENT_TEXTS}
    response = all_intent_texts.get(intent, "Я здесь, чтобы помочь! 🤗")
    
    await reply_with_text_and_log(message, user_id, response)

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
        welcome_message = render_welcome_detailed(first_name)
        await message.reply(welcome_message)
        return
    
    # Проверяем лимит сообщений и увеличиваем счетчик
    can_proceed = await check_and_increment_daily_limit(user_id, message)
    if not can_proceed:
        return
    
    # Добавляем сообщение пользователя в историю
    add_to_conversation_history(user_id, 'user', user_message)
    
    # Упрощенная обработка - используем только GPT для определения ответа
    try:
        await handle_unified_message(message, user_id, user_message)
            
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