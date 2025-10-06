# Планировщик ежедневных уведомлений

import asyncio
import logging
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from storage.db import get_all_users
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

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
    
    def start(self, reminder_time: time = time(10, 0)):
        """Запуск планировщика с ежедневными напоминаниями"""
        # Добавляем задачу на отправку ежедневных напоминаний
        self.scheduler.add_job(
            self.send_daily_reminders,
            CronTrigger(hour=reminder_time.hour, minute=reminder_time.minute),
            id='daily_reminder',
            name='Ежедневное напоминание пользователям',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info(f"Планировщик запущен. Ежедневные напоминания в {reminder_time.strftime('%H:%M')}")
    
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