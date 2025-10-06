from openai import AsyncOpenAI
import os
import httpx
from dotenv import load_dotenv
from pathlib import Path

# Загрузка переменных окружения из .env файла
load_dotenv()

# Глобальный клиент OpenAI
_openai_client = None
_http_client = None

def get_openai_client():
    """Получает или создает глобальный клиент OpenAI"""
    global _openai_client, _http_client
    if _openai_client is None:
        # Создаем собственный httpx клиент
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        _openai_client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            http_client=_http_client
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

async def chat_with_gpt(prompt: str, model: str = "gpt-4o-mini", conversation_history: list = None) -> str:
    """
    Отправляет запрос к ChatGPT и возвращает ответ.

    :param prompt: Текст запроса для ChatGPT.
    :param model: Модель ChatGPT (по умолчанию "gpt-4o-mini").
    :param conversation_history: История разговора для контекста.
    :return: Ответ от ChatGPT.
    """
    client = get_openai_client()
    
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

async def close_openai_client():
    """Закрывает глобальный OpenAI клиент"""
    global _openai_client, _http_client
    if _openai_client:
        try:
            await _openai_client.close()
        except Exception as e:
            print(f"Ошибка при закрытии OpenAI клиента: {e}")
        finally:
            _openai_client = None
    
    if _http_client:
        try:
            await _http_client.aclose()
        except Exception as e:
            print(f"Ошибка при закрытии HTTP клиента: {e}")
        finally:
            _http_client = None