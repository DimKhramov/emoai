#!/usr/bin/env python3
"""
Менеджер системы оплаты через Telegram Stars
Отдельный скрипт для управления премиум подписками и балансом звезд
"""

import os
import asyncio
from datetime import date, timedelta
from aiogram import Bot, types
from aiogram.types import LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

from storage.db import (
    get_user_premium_status, activate_premium_subscription,
    get_all_premium_users, get_user_by_telegram_id,
    set_auto_renewal
)

# Загрузка переменных окружения
load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
bot = Bot(token=API_TOKEN)

# Конфигурация цен (в звездах Telegram)
PREMIUM_PRICES = {
    "monthly": {"stars": 100, "days": 30, "title": "Премиум на месяц"},
    "weekly": {"stars": 30, "days": 7, "title": "Премиум на неделю"},
    "daily": {"stars": 10, "days": 1, "title": "Премиум на день"}
}

def create_star_invoice(title: str, description: str, payload: str, star_count: int) -> dict:
    """
    Создает данные для инвойса оплаты звездами Telegram
    
    Args:
        title: Заголовок товара
        description: Описание товара
        payload: Полезная нагрузка для идентификации платежа
        star_count: Количество звезд для оплаты
    
    Returns:
        Словарь с данными инвойса
    """
    return {
        "title": title,
        "description": description,
        "payload": payload,
        "star_count": star_count
    }

def process_successful_payment(user_id: int, payment_charge_id: str, total_amount: int) -> bool:
    """
    Обрабатывает успешный платеж и активирует премиум подписку
    
    Args:
        user_id: ID пользователя в Telegram
        payment_charge_id: ID платежа в Telegram
        total_amount: Сумма платежа в звездах
    
    Returns:
        True если платеж обработан успешно, False в противном случае
    """
    try:
        # Определяем тип подписки по сумме
        days = 30  # По умолчанию месяц
        if total_amount == 10:
            days = 1
        elif total_amount == 30:
            days = 7
        elif total_amount == 100:
            days = 30
        
        # Активируем премиум подписку
        activate_premium_subscription(user_id, days)
        
        # Убираем бонусные звезды - ничего не должно поступать на баланс
        # bonus_stars = total_amount // 10  # 10% бонус
        # if bonus_stars > 0:
        #     update_stars_balance(user_id, bonus_stars)
        
        return True
    except Exception as e:
        print(f"Ошибка при обработке платежа: {e}")
        return False

def get_user_payment_info(user_id: int) -> dict:
    """
    Получает информацию о платежах пользователя
    
    Args:
        user_id: ID пользователя в Telegram
    
    Returns:
        Словарь с информацией о платежах
    """
    return get_user_premium_status(user_id)

async def send_premium_offer(bot: Bot, user_id: int):
    """
    Отправляет предложение о покупке премиум подписки
    
    Args:
        bot: Экземпляр бота
        user_id: ID пользователя в Telegram
    """
    # Получаем информацию о пользователе для проверки статуса автопродления
    user_info = get_user_premium_status(user_id)
    auto_renewal_status = user_info.get('auto_renewal', False) if user_info else False
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌟 День • 10 ⭐", callback_data="buy_premium_daily"),
            InlineKeyboardButton(text="✨ Неделя • 30 ⭐", callback_data="buy_premium_weekly")
        ],
        [
            InlineKeyboardButton(text="💎 МЕСЯЦ • 100 ⭐ 🔥", callback_data="buy_premium_monthly")
        ],
        [
            InlineKeyboardButton(text="💰 Проверить баланс", callback_data="check_balance")
        ],
        [
            InlineKeyboardButton(
                text=f"🔄 Автопродление: {'✅ ВКЛ' if auto_renewal_status else '❌ ВЫКЛ'}", 
                callback_data="toggle_auto_renewal"
            )
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
        ]
    ])
    
    auto_renewal_text = ""
    if auto_renewal_status:
        auto_renewal_text = "\n🔄 *Автопродление включено* - подписка будет автоматически продлеваться каждый месяц за 100 ⭐"
    
    offer_text = (
        "🌟 ПРЕМИУМ ПОДПИСКА 🌟\n\n"
        "🎯 Что вы получите:\n"
        "• 🚀 Безлимитные сообщения\n"
        "• ⚡ Приоритетная обработка\n"
        "• 🎨 Расширенные функции\n"
        "• 💎 Эксклюзивный контент\n\n"
        "💰 Тарифы:\n"
        "🌟 День: 10 ⭐ (экономия 0%)\n"
        "✨ Неделя: 30 ⭐ (экономия 57%)\n"
        "💎 МЕСЯЦ: 100 ⭐ (экономия 67%) 🔥\n\n"
        "🔥 Самый выгодный тариф - МЕСЯЦ!\n"
        f"{auto_renewal_text}\n"
        "Выберите подходящий план:"
    )
    
    await bot.send_message(
        chat_id=user_id,
        text=offer_text,
        reply_markup=keyboard
    )

async def send_premium_reminder(bot: Bot, user_id: int, days_left: int):
    """
    Отправляет напоминание о скором окончании премиум подписки
    
    Args:
        bot: Экземпляр бота
        user_id: ID пользователя в Telegram
        days_left: Количество дней до окончания подписки
    """
    if days_left <= 3:
        reminder_text = (
            f"⚠️ Внимание!\n\n"
            f"Ваша премиум подписка истекает через {days_left} дн.\n\n"
            f"🔄 Продлите подписку, чтобы не потерять:\n"
            f"• Безлимитные сообщения\n"
            f"• Приоритетную поддержку\n"
            f"• Расширенные функции\n\n"
            f"Используйте /premium для продления"
        )
        
        await bot.send_message(
            chat_id=user_id,
            text=reminder_text
        )

def get_premium_stats() -> dict:
    """
    Получает статистику по премиум пользователям
    
    Returns:
        Словарь со статистикой
    """
    premium_users = get_all_premium_users()
    
    total_premium = len(premium_users)
    
    return {
        "total_premium_users": total_premium,
        "premium_users": premium_users
    }

class PaymentManager:
    """Класс для управления системой оплаты"""
    
    def __init__(self):
        self.bot = bot
    
    async def create_star_invoice(self, user_id: int, plan: str = "monthly") -> types.Message:
        """
        Создает инвойс для оплаты звездами Telegram
        
        Args:
            user_id: ID пользователя в Telegram
            plan: Тип подписки (monthly, weekly, daily)
        
        Returns:
            Сообщение с инвойсом
        """
        if plan not in PREMIUM_PRICES:
            raise ValueError(f"Неизвестный план: {plan}")
        
        plan_info = PREMIUM_PRICES[plan]
        
        return await self.bot.send_invoice(
            chat_id=user_id,
            title=plan_info["title"],
            description=f"Премиум подписка на {plan_info['days']} дней",
            payload=f"premium_{plan}_{user_id}",
            provider_token="",  # Для Telegram Stars не нужен
            currency="XTR",  # Telegram Stars
            prices=[LabeledPrice(label=plan_info["title"], amount=plan_info["stars"])]
        )
    
    async def process_successful_payment(self, user_id: int, plan: str):
        """
        Обрабатывает успешный платеж
        
        Args:
            user_id: ID пользователя в Telegram
            plan: Тип подписки
        """
        if plan not in PREMIUM_PRICES:
            return False
        
        plan_info = PREMIUM_PRICES[plan]
        
        # Активируем премиум подписку
        activate_premium_subscription(user_id, plan_info["days"])
        
        # Убираем бонусные звезды - ничего не должно поступать на баланс
        # bonus_stars = plan_info["stars"] // 10  # 10% бонус
        # if bonus_stars > 0:
        #     update_stars_balance(user_id, bonus_stars)
        
        return True
    
    async def get_user_payment_info(self, user_id: int) -> str:
        """
        Получает информацию о платежах пользователя в виде текста
        
        Args:
            user_id: ID пользователя в Telegram
        
        Returns:
            Текстовая информация о платежах
        """
        info = get_user_premium_status(user_id)
        
        if not info:
            return "❌ Информация о платежах недоступна"
        
        status_text = "✅ Активна" if info['premium_status'] else "❌ Неактивна"
        
        return (
            f"💰 *Информация о платежах:*\n\n"
            f"👑 Премиум статус: {status_text}\n"
            f"📅 Подписка до: {info['subscription_end_date'] or 'Не активна'}"
        )
    
    async def send_premium_offer(self, user_id: int):
        """
        Отправляет предложение о покупке премиум подписки
        
        Args:
            user_id: ID пользователя в Telegram
        """
        await send_premium_offer(self.bot, user_id)
    
    async def toggle_auto_renewal(self, user_id: int, enabled: bool) -> bool:
        """
        Включает или отключает автоматическое продление подписки
        
        Args:
            user_id: ID пользователя в Telegram
            enabled: True для включения, False для отключения
        
        Returns:
            True если операция успешна, False в противном случае
        """
        try:
            set_auto_renewal(user_id, enabled)
            return True
        except Exception as e:
            print(f"Ошибка при изменении настроек автопродления: {e}")
            return False

# Функции для экспорта
async def main():
    """Основная функция для тестирования"""
    manager = PaymentManager()
    
    # Пример использования
    stats = get_premium_stats()
    print(f"Статистика премиум пользователей: {stats}")

if __name__ == "__main__":
    asyncio.run(main())