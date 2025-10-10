# Планировщик ежедневных уведомлений и автоматических платежей

import asyncio
import logging
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from storage.db import get_all_users, get_users_for_auto_renewal, process_auto_renewal, get_users_for_renewal_reminder
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from config import SchedulerConfig

logger = logging.getLogger(__name__)

class DailyReminderScheduler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.reminder_messages = [
            "Привет! 😊 Как дела? Расскажи, что у тебя на душе сегодня?",
            "Доброе утро! ☀️ Как твоё настроение? Я здесь, чтобы выслушать тебя.",
            "Привет! 🌟 Хочешь поделиться своими мыслями? Я всегда готов поговорить.",
            "Как дела? 💭 Если что-то беспокоит или радует - расскажи мне об этом!",
            "Привет! 🤗 Помни, что я всегда здесь для тебя. Как прошёл твой день?",
            "Доброе утро! 🌸 Какие эмоции ты испытываешь сегодня? Поделись со мной!",
            "Привет! ✨ Хочешь просто поговорить? Я готов выслушать всё, что у тебя на сердце."
        ]
    
    def start(self, reminder_time: time = None):
        """Запуск планировщика с ежедневными напоминаниями и автоматическими платежами"""
        # Используем время из конфигурации, если не передано явно
        if reminder_time is None:
            reminder_time = SchedulerConfig.DAILY_REMINDER_TIME
            
        # Добавляем задачу на отправку ежедневных напоминаний
        self.scheduler.add_job(
            self.send_daily_reminders,
            CronTrigger(hour=reminder_time.hour, minute=reminder_time.minute),
            id='daily_reminder',
            name='Ежедневное напоминание пользователям',
            replace_existing=True
        )
        
        # Добавляем задачу на отправку напоминаний о предстоящем автосписании
        self.scheduler.add_job(
            self.send_renewal_reminders,
            CronTrigger(hour=SchedulerConfig.RENEWAL_REMINDER_HOUR, minute=SchedulerConfig.RENEWAL_REMINDER_MINUTE),
            id='renewal_reminder',
            name='Напоминания о предстоящем автосписании',
            replace_existing=True
        )
        
        # Добавляем задачу на автоматическое продление подписок
        self.scheduler.add_job(
            self.process_auto_renewals,
            CronTrigger(hour=SchedulerConfig.AUTO_RENEWAL_HOUR, minute=SchedulerConfig.AUTO_RENEWAL_MINUTE),
            id='auto_renewal',
            name='Автоматическое продление подписок',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info(f"Планировщик запущен. Ежедневные напоминания в {reminder_time.strftime('%H:%M')}, напоминания об автосписании в {SchedulerConfig.RENEWAL_REMINDER_HOUR:02d}:{SchedulerConfig.RENEWAL_REMINDER_MINUTE:02d}, автопродление в {SchedulerConfig.AUTO_RENEWAL_HOUR:02d}:{SchedulerConfig.AUTO_RENEWAL_MINUTE:02d}")
    
    def stop(self):
        """Остановка планировщика"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Планировщик остановлен")
    
    async def send_daily_reminders(self):
        """Отправка ежедневных напоминаний всем пользователям"""
        try:
            users = get_all_users()
            if not users:
                logger.info("Нет пользователей для отправки напоминаний")
                return
            
            import random
            message = random.choice(self.reminder_messages)
            
            sent_count = 0
            failed_count = 0
            
            for user in users:
                try:
                    await self.bot.send_message(
                        chat_id=user['telegram_id'],
                        text=message
                    )
                    sent_count += 1
                    # Небольшая задержка между отправками
                    await asyncio.sleep(0.1)
                    
                except TelegramForbiddenError:
                    # Пользователь заблокировал бота
                    logger.warning(f"Пользователь {user['telegram_id']} заблокировал бота")
                    failed_count += 1
                    
                except TelegramBadRequest as e:
                    # Неверный chat_id или другая ошибка
                    logger.warning(f"Ошибка отправки пользователю {user['telegram_id']}: {e}")
                    failed_count += 1
                    
                except Exception as e:
                    logger.error(f"Неожиданная ошибка при отправке пользователю {user['telegram_id']}: {e}")
                    failed_count += 1
            
            logger.info(f"Ежедневные напоминания отправлены: {sent_count} успешно, {failed_count} неудачно")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке ежедневных напоминаний: {e}")
    
    async def send_test_reminder(self, user_id: int):
        """Отправка тестового напоминания конкретному пользователю"""
        try:
            import random
            message = random.choice(self.reminder_messages)
            await self.bot.send_message(chat_id=user_id, text=message)
            logger.info(f"Тестовое напоминание отправлено пользователю {user_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки тестового напоминания пользователю {user_id}: {e}")
            return False
    
    async def process_auto_renewals(self):
        """Обработка автоматических продлений подписок"""
        try:
            users_for_renewal = get_users_for_auto_renewal()
            if not users_for_renewal:
                logger.info("Нет пользователей для автоматического продления подписок")
                return
            
            renewed_count = 0
            failed_count = 0
            insufficient_funds_count = 0
            
            for user in users_for_renewal:
                user_id = user['telegram_id']
                
                try:
                    # process_auto_renewal теперь сам определяет стоимость по типу подписки
                    success = process_auto_renewal(user_id)
                    if success:
                        renewed_count += 1
                        # Уведомляем пользователя об успешном продлении
                        await self.bot.send_message(
                            chat_id=user_id,
                            text="✅ Ваша премиум подписка автоматически продлена!\n"
                                 "Спасибо за использование нашего сервиса! 💫"
                        )
                    else:
                        failed_count += 1
                        # Уведомляем пользователя о проблеме с продлением
                        await self.bot.send_message(
                            chat_id=user_id,
                            text="⚠️ Не удалось автоматически продлить премиум подписку!\n\n"
                                 "Используйте /premium для управления подпиской."
                        )
                        
                except TelegramForbiddenError:
                    logger.warning(f"Пользователь {user_id} заблокировал бота")
                    failed_count += 1
                except Exception as e:
                    logger.error(f"Ошибка при обработке автопродления для пользователя {user_id}: {e}")
                    failed_count += 1
            
            logger.info(f"Автопродление завершено. Продлено: {renewed_count}, Ошибок: {failed_count}, Недостаточно средств: {insufficient_funds_count}")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке автопродлений: {e}")

    async def send_renewal_reminders(self):
        """Отправка напоминаний о предстоящем автоматическом списании"""
        try:
            users = get_users_for_renewal_reminder()
            
            if not users:
                logger.info("Нет пользователей для отправки напоминаний об автосписании")
                return
            
            sent_count = 0
            failed_count = 0
            
            for user in users:
                try:
                    user_id = user['telegram_id']
                    subscription_end = user['subscription_end_date']
                    
                    # Формируем сообщение о предстоящем автопродлении
                    message = (
                        "🔔 Напоминание об автопродлении\n\n"
                        f"📅 Ваша премиум подписка истекает {subscription_end}\n\n"
                        "✅ Через 3 дня подписка будет автоматически продлена на месяц.\n\n"
                        "Если хотите отключить автопродление, используйте /premium"
                    )
                    
                    await self.bot.send_message(chat_id=user_id, text=message)
                    sent_count += 1
                    
                except TelegramForbiddenError:
                    logger.warning(f"Пользователь {user_id} заблокировал бота")
                    failed_count += 1
                except Exception as e:
                    logger.error(f"Ошибка при отправке напоминания пользователю {user_id}: {e}")
                    failed_count += 1
            
            logger.info(f"Напоминания об автосписании отправлены. Успешно: {sent_count}, Ошибок: {failed_count}")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке напоминаний об автосписании: {e}")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке автоматических продлений: {e}")