# Emotional Friend Bot

Телеграм-бот для эмоциональной поддержки с ежедневными напоминаниями и AI-помощником.

## Функции

- 🤖 AI-помощник для эмоциональной поддержки
- 📅 Ежедневные напоминания о заботе о себе
- 📊 Статистика использования
- 💭 Ведение дневника эмоций
- 🎯 Микрошаги для улучшения настроения

## Деплой на Replit

### 1. Подготовка

1. Создайте аккаунт на [Replit.com](https://replit.com)
2. Нажмите "Create Repl"
3. Выберите "Import from GitHub"
4. Вставьте URL вашего GitHub репозитория

### 2. Настройка переменных окружения

В Replit перейдите в раздел "Secrets" (🔒) и добавьте:

```
TELEGRAM_API_TOKEN=ваш_токен_бота
OPENAI_API_KEY=ваш_ключ_openai
REMINDER_HOUR=10
REMINDER_MINUTE=0
ENABLE_DAILY_REMINDERS=true
TIMEZONE=Europe/Moscow
LOG_LEVEL=INFO
```

### 3. Запуск

1. Replit автоматически установит зависимости из `requirements.txt`
2. Нажмите кнопку "Run" или выполните `python app.py`
3. Бот запустится и будет доступен 24/7

### 4. Мониторинг

- Логи отображаются в консоли Replit
- Для постоянной работы используйте Replit Hacker Plan
- Поддерживается автоматический перезапуск

## Деплой на Railway

### 1. Подготовка

1. Создайте аккаунт на [Railway.app](https://railway.app)
2. Подключите ваш GitHub аккаунт
3. Загрузите код в GitHub репозиторий

### 2. Создание проекта

1. Войдите в Railway Dashboard
2. Нажмите "New Project"
3. Выберите "Deploy from GitHub repo"
4. Выберите ваш репозиторий

### 3. Настройка переменных окружения

В Railway Dashboard добавьте следующие переменные:

```
TELEGRAM_API_TOKEN=ваш_токен_бота
OPENAI_API_KEY=ваш_ключ_openai
REMINDER_HOUR=10
REMINDER_MINUTE=0
ENABLE_DAILY_REMINDERS=true
TIMEZONE=Europe/Moscow
LOG_LEVEL=INFO
```

### 4. Деплой

1. Railway автоматически определит Python проект
2. Установит зависимости из `requirements.txt`
3. Запустит приложение командой `python app.py`

### 5. Мониторинг

- Логи доступны в Railway Dashboard
- Бот будет автоматически перезапускаться при сбоях

## Альтернативный деплой на Replit

**Рекомендуется для избежания проблем с зависимостями!**

### Быстрый старт:

1. Перейдите на [Replit.com](https://replit.com)
2. Создайте новый Repl → "Import from GitHub"
3. Вставьте URL вашего репозитория
4. Добавьте переменные окружения в "Secrets":
   - `TELEGRAM_BOT_TOKEN`
   - `OPENAI_API_KEY`
5. Нажмите "Run"

📖 **Подробные инструкции:** см. [REPLIT_DEPLOY.md](REPLIT_DEPLOY.md)

### Преимущества Replit:
- ✅ Нет проблем с кэшированием зависимостей
- ✅ Встроенная IDE для разработки
- ✅ Простое развертывание одним кликом
- ✅ Автоматическое управление зависимостями
- Поддерживается автоматический деплой при push в GitHub

## Локальная разработка

1. Клонируйте репозиторий
2. Создайте файл `.env` с переменными окружения
3. Установите зависимости: `pip install -r requirements.txt`
4. Запустите: `python app.py`

## Команды бота

- `/start` - Начать работу с ботом
- `/help` - Показать справку
- `/journal` - Записать в дневник эмоций
- `/microsteps` - Получить микрошаги
- `/stats` - Показать статистику
- `/test_reminder` - Тестировать уведомления

## Технологии

- Python 3.11+
- aiogram 3.x (Telegram Bot API)
- OpenAI GPT API
- APScheduler (планировщик задач)
- SQLite (база данных)
- Railway (хостинг)