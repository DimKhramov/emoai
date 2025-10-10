"""
Обработчик команд для управления пользовательскими предпочтениями
"""

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from storage.db import get_user_preferences, update_user_preferences

router = Router()

@router.message(Command("settings", "настройки"))
async def show_settings(message: Message):
    """Показывает текущие настройки пользователя"""
    user_id = message.from_user.id
    preferences = get_user_preferences(user_id)
    
    # Формируем текст с текущими настройками
    emoji_status = "✅ Включены" if preferences['use_emojis'] else "❌ Отключены"
    
    style_map = {
        'friendly': '😊 Дружелюбный',
        'formal': '📝 Формальный', 
        'casual': '😎 Неформальный'
    }
    style_status = style_map.get(preferences['communication_style'], '😊 Дружелюбный')
    
    length_map = {
        'short': '📏 Краткие',
        'medium': '📖 Средние',
        'long': '📚 Подробные'
    }
    length_status = length_map.get(preferences['preferred_response_length'], '📖 Средние')
    
    settings_text = f"""⚙️ **Твои настройки общения:**

🎭 **Эмодзи:** {emoji_status}
💬 **Стиль общения:** {style_status}
📝 **Длина ответов:** {length_status}

Выбери, что хочешь изменить:"""
    
    # Создаем клавиатуру с настройками
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎭 Эмодзи", callback_data="settings_emojis")],
        [InlineKeyboardButton(text="💬 Стиль общения", callback_data="settings_style")],
        [InlineKeyboardButton(text="📝 Длина ответов", callback_data="settings_length")],
        [InlineKeyboardButton(text="🔄 Сбросить все", callback_data="settings_reset")]
    ])
    
    await message.reply(settings_text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "settings_emojis")
async def toggle_emojis(callback: CallbackQuery):
    """Переключает использование эмодзи"""
    user_id = callback.from_user.id
    preferences = get_user_preferences(user_id)
    
    new_emoji_setting = not preferences['use_emojis']
    update_user_preferences(user_id, use_emojis=new_emoji_setting)
    
    status = "включены" if new_emoji_setting else "отключены"
    await callback.answer(f"Эмодзи {status}!")
    
    # Обновляем сообщение с настройками
    await show_settings_after_change(callback.message, user_id)

@router.callback_query(F.data == "settings_style")
async def change_style(callback: CallbackQuery):
    """Показывает варианты стиля общения"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="😊 Дружелюбный", callback_data="style_friendly")],
        [InlineKeyboardButton(text="📝 Формальный", callback_data="style_formal")],
        [InlineKeyboardButton(text="😎 Неформальный", callback_data="style_casual")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="settings_back")]
    ])
    
    await callback.message.edit_text(
        "💬 **Выбери стиль общения:**\n\n"
        "😊 **Дружелюбный** — тёплый, понимающий\n"
        "📝 **Формальный** — вежливый, без сленга\n"
        "😎 **Неформальный** — расслабленный, со сленгом",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("style_"))
async def set_style(callback: CallbackQuery):
    """Устанавливает стиль общения"""
    user_id = callback.from_user.id
    style = callback.data.replace("style_", "")
    
    update_user_preferences(user_id, communication_style=style)
    
    style_names = {
        'friendly': 'дружелюбный',
        'formal': 'формальный',
        'casual': 'неформальный'
    }
    
    await callback.answer(f"Стиль изменён на {style_names[style]}!")
    await show_settings_after_change(callback.message, user_id)

@router.callback_query(F.data == "settings_length")
async def change_length(callback: CallbackQuery):
    """Показывает варианты длины ответов"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📏 Краткие", callback_data="length_short")],
        [InlineKeyboardButton(text="📖 Средние", callback_data="length_medium")],
        [InlineKeyboardButton(text="📚 Подробные", callback_data="length_long")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="settings_back")]
    ])
    
    await callback.message.edit_text(
        "📝 **Выбери длину ответов:**\n\n"
        "📏 **Краткие** — 1-2 предложения\n"
        "📖 **Средние** — 2-4 предложения\n"
        "📚 **Подробные** — развёрнутые ответы",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("length_"))
async def set_length(callback: CallbackQuery):
    """Устанавливает длину ответов"""
    user_id = callback.from_user.id
    length = callback.data.replace("length_", "")
    
    update_user_preferences(user_id, preferred_response_length=length)
    
    length_names = {
        'short': 'краткие',
        'medium': 'средние',
        'long': 'подробные'
    }
    
    await callback.answer(f"Длина ответов изменена на {length_names[length]}!")
    await show_settings_after_change(callback.message, user_id)

@router.callback_query(F.data == "settings_reset")
async def reset_settings(callback: CallbackQuery):
    """Сбрасывает настройки к значениям по умолчанию"""
    user_id = callback.from_user.id
    
    update_user_preferences(
        user_id,
        use_emojis=True,
        communication_style='friendly',
        preferred_response_length='medium'
    )
    
    await callback.answer("Настройки сброшены!")
    await show_settings_after_change(callback.message, user_id)

@router.callback_query(F.data == "settings_back")
async def back_to_settings(callback: CallbackQuery):
    """Возвращает к главному меню настроек"""
    await show_settings_after_change(callback.message, callback.from_user.id)

async def show_settings_after_change(message: Message, user_id: int):
    """Обновляет сообщение с настройками после изменения"""
    preferences = get_user_preferences(user_id)
    
    # Формируем текст с текущими настройками
    emoji_status = "✅ Включены" if preferences['use_emojis'] else "❌ Отключены"
    
    style_map = {
        'friendly': '😊 Дружелюбный',
        'formal': '📝 Формальный', 
        'casual': '😎 Неформальный'
    }
    style_status = style_map.get(preferences['communication_style'], '😊 Дружелюбный')
    
    length_map = {
        'short': '📏 Краткие',
        'medium': '📖 Средние',
        'long': '📚 Подробные'
    }
    length_status = length_map.get(preferences['preferred_response_length'], '📖 Средние')
    
    settings_text = f"""⚙️ **Твои настройки общения:**

🎭 **Эмодзи:** {emoji_status}
💬 **Стиль общения:** {style_status}
📝 **Длина ответов:** {length_status}

Выбери, что хочешь изменить:"""
    
    # Создаем клавиатуру с настройками
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎭 Эмодзи", callback_data="settings_emojis")],
        [InlineKeyboardButton(text="💬 Стиль общения", callback_data="settings_style")],
        [InlineKeyboardButton(text="📝 Длина ответов", callback_data="settings_length")],
        [InlineKeyboardButton(text="🔄 Сбросить все", callback_data="settings_reset")]
    ])
    
    await message.edit_text(settings_text, reply_markup=keyboard, parse_mode="Markdown")