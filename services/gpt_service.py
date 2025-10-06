from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
from pathlib import Path

# Загрузка переменных окружения из .env файла
load_dotenv()

def load_system_prompt() -> str:
    """Загружает системный промпт из файла"""
    prompt_path = Path(__file__).parent.parent / "prompts" / "system_prompt.txt"
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "Ты — «Эмо-друг», ИИ-агент в Телеграме. Будь поддерживающим и эмоциональным собеседником."

async def chat_with_gpt(prompt: str, model: str = "gpt-4o-mini", conversation_history: list = None) -> str:
    """
    Отправляет запрос к ChatGPT и возвращает ответ.

    :param prompt: Текст запроса для ChatGPT.
    :param model: Модель ChatGPT (по умолчанию "gpt-4o-mini").
    :param conversation_history: История разговора для контекста.
    :return: Ответ от ChatGPT.
    """
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Загружаем системный промпт
    system_prompt = load_system_prompt()
    
    # Формируем сообщения
    messages = [{"role": "system", "content": system_prompt}]
    
    # Добавляем историю разговора если есть
    if conversation_history:
        messages.extend(conversation_history[-10:])  # Берем последние 10 сообщений
    
    # Добавляем текущий запрос
    messages.append({"role": "user", "content": prompt})

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.8,  # Делаем ответы более креативными
            max_tokens=500    # Ограничиваем длину ответа
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Ошибка GPT API: {e}")
        return "Извини, у меня сейчас проблемы с ответом. Попробуй еще раз! 😅"