# Интеграция с Telegram через aiogram

import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv
from services.intents import determine_intent
from services.journal import create_journal_entry
from services.microsteps import MICROSTEPS
from storage.db import (
    initialize_database, add_user, get_user_by_telegram_id, 
    is_new_user, add_message, get_conversation_history, 
    clear_conversation_history, get_user_stats
)
from services.gpt_service import chat_with_gpt

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
    help_text = "🤖 **Доступные команды:**\n\n" \
               "• /start - Начать общение\n" \
               "• /help - Показать эту справку\n" \
               "• /stats - Показать статистику\n" \
               "• /clear - Очистить историю чата\n" \
               "• /test_reminder - Протестировать уведомления\n\n" \
               "Просто напиши мне что-нибудь, и я отвечу! 😊\n\n" \
               "🔔 **Ежедневные напоминания:** Каждый день в 10:00 я буду напоминать тебе о возможности пообщаться!"
    
    await message.answer(help_text, parse_mode='Markdown')

@dp.message(Command('stats'))
async def stats_command(message: Message):
    """Обработчик команды /stats"""
    user_id = message.from_user.id
    
    # Получаем данные пользователя из БД
    user = get_user_by_telegram_id(user_id)
    
    if user:
        stats = get_user_stats(user['id'])
        stats_text = f"📊 **Твоя статистика:**\n\n" \
                    f"• Сообщений отправлено: {stats['message_count']}\n" \
                    f"• Зарегистрирован: {user['created_at']}\n" \
                    f"• Последняя активность: {stats['last_activity'] or 'Неизвестно'}"
    else:
        stats_text = "📊 Статистика пока недоступна. Начни общение командой /start!"
    
    await message.answer(stats_text, parse_mode='Markdown')

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

async def get_gpt_response(user_id: int, user_message: str) -> str:
    """Получение ответа от GPT с историей разговора"""
    user = get_user_by_telegram_id(user_id)
    conversation_history = get_conversation_history(user['id']) if user else []
    gpt_history = [{'role': msg['role'], 'content': msg['content']} for msg in conversation_history]
    return await chat_with_gpt(user_message, conversation_history=gpt_history)

async def handle_talk_intent(message: Message, user_id: int, user_message: str):
    """Обработка интента talk"""
    response = await get_gpt_response(user_id, user_message)
    if not response:
        response = "Привет! Как ты себя чувствуешь? 😊 Расскажи мне что у тебя на душе!"
    await message.reply(response)
    add_to_conversation_history(user_id, 'assistant', response)

async def handle_other_intent(message: Message, user_id: int, user_message: str):
    """Обработка неопознанных интентов"""
    response = await get_gpt_response(user_id, user_message)
    if not response:
        response = "Я здесь, чтобы помочь! Расскажи, что у тебя на уме. 🤗"
    await message.reply(response)
    add_to_conversation_history(user_id, 'assistant', response)

async def handle_simple_intent(message: Message, user_id: int, intent: str):
    """Обработка простых интентов с предопределенными ответами"""
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
    """Обработка всех текстовых сообщений"""
    user_id = message.from_user.id
    user_message = message.text
    
    if not user_message:
        await message.reply("Пожалуйста, отправьте текстовое сообщение 📝")
        return
    
    # Инициализируем пользователя если нужно
    ensure_user_initialized(user_id, message.from_user.username, message.from_user.first_name)
    
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