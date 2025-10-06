import os
import json
import requests
from dotenv import load_dotenv
from pathlib import Path
import asyncio

load_dotenv()

def make_openai_request(messages, model="gpt-4o-mini", max_tokens=1000, temperature=0.7):
    """Прямой HTTP запрос к OpenAI API без использования SDK"""
    api_key = os.getenv("OPENAI_API_KEY")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=30
    )
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")

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
        
        # Выполняем HTTP запрос в отдельном потоке
        def sync_request():
            return make_openai_request(messages)
        
        response = await asyncio.to_thread(sync_request)
        return response
        
    except Exception as e:
        print(f"Ошибка при обращении к GPT: {e}")
        return "Извините, произошла ошибка при обработке вашего сообщения. Попробуйте еще раз."

def close_openai_client():
    """Заглушка для совместимости - клиенты создаются для каждого запроса"""
    pass