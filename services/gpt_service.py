import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import asyncio

load_dotenv()

# Глобальный клиент OpenAI
_openai_client = None

def get_openai_client():
    """Получает или создает клиент OpenAI"""
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY не найден в переменных окружения")
        
        _openai_client = OpenAI(
            api_key=api_key,
            timeout=30.0
        )
    return _openai_client

def load_system_prompt() -> str:
    """Загружает системный промпт из файла"""
    prompt_path = Path(__file__).parent.parent / "prompts" / "system_prompt.txt"
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "Ты — «Эмо-друг», ИИ-агент в Телеграме. Будь поддерживающим и эмоциональным собеседником."

async def chat_with_gpt(user_message, user_id=None):
    """Отправляет сообщение в GPT и возвращает ответ"""
    try:
        # Загружаем системный промпт
        system_prompt = load_system_prompt()
        
        # Формируем сообщения
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # Получаем клиент и выполняем запрос в отдельном потоке
        def sync_request():
            client = get_openai_client()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        
        response = await asyncio.to_thread(sync_request)
        return response
        
    except Exception as e:
        print(f"Ошибка при обращении к GPT: {e}")
        return "Извините, произошла ошибка при обработке вашего сообщения. Попробуйте еще раз."

def close_openai_client():
    """Закрывает OpenAI клиент"""
    global _openai_client
    if _openai_client is not None:
        try:
            _openai_client.close()
        except Exception as e:
            print(f"Ошибка при закрытии OpenAI клиента: {e}")
        finally:
            _openai_client = None