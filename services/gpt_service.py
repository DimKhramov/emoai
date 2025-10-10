import os
import random
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import asyncio
from config import OpenAIConfig
from .dynamic_response import get_response_config, analyze_conversation_context, get_style_instructions, format_response_config_info

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
            timeout=OpenAIConfig.TIMEOUT
        )
    return _openai_client



def detect_emotion_keywords(text: str) -> str:
    """Определяет эмоциональное состояние сообщения с помощью GPT"""
    try:
        client = get_openai_client()
        
        prompt = f"""Проанализируй эмоциональное состояние следующего сообщения и верни ТОЛЬКО одно слово из списка:
- sos (если есть угроза жизни, суицидальные мысли, насилие)
- anger (злость, ярость, раздражение)
- sadness (грусть, печаль, депрессия)
- tired (усталость, выгорание, истощение)
- provocation (оскорбления, провокации)
- generic (общие разговорные темы с эмоциональным подтекстом)
- neutral (обычные вопросы, нейтральные темы без эмоций)

Сообщение: "{text}"

Ответ:"""

        response = client.chat.completions.create(
            model=OpenAIConfig.MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=OpenAIConfig.MAX_TOKENS,
            temperature=OpenAIConfig.TEMPERATURE
        )
        
        emotion = response.choices[0].message.content.strip().lower()
        
        # Проверяем, что ответ валидный
        valid_emotions = ["sos", "anger", "sadness", "tired", "provocation", "generic", "neutral"]
        if emotion in valid_emotions:
            return emotion
        else:
            return "neutral"  # По умолчанию нейтральное
            
    except Exception as e:
        print(f"Ошибка при определении эмоции через GPT: {e}")
        
        # Fallback к простой проверке ключевых слов
        text_lower = text.lower()
        
        # Базовые ключевые слова для критических случаев
        sos_keywords = ["не хочу жить", "покончить", "самоуб", "суицид", "убью себя"]
        anger_keywords = ["бесит", "злюсь", "ярость", "убить", "достало"]
        sadness_keywords = ["грустно", "тяжело", "печаль", "разбито", "пусто"]
        tired_keywords = ["устал", "выгорел", "нет сил", "измотан"]
        
        if any(keyword in text_lower for keyword in sos_keywords):
            return "sos"
        elif any(keyword in text_lower for keyword in anger_keywords):
            return "anger"
        elif any(keyword in text_lower for keyword in sadness_keywords):
            return "sadness"
        elif any(keyword in text_lower for keyword in tired_keywords):
            return "tired"
        else:
            return "neutral"



def load_system_prompt() -> str:
    """Загружает системный промпт из файла"""
    prompt_path = Path(__file__).parent.parent / "prompts" / "system_prompt.txt"
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "Ты дружелюбный помощник, который поддерживает пользователей в сложных ситуациях."

async def chat_with_gpt(user_message, user_id=None, conversation_history=None):
    """Отправляет сообщение в GPT и получает ответ с динамической длиной"""
    try:
        client = get_openai_client()
        
        # Определяем эмоциональное состояние сообщения
        emotion_type = detect_emotion_keywords(user_message)
        
        # Анализируем контекст разговора
        context_type = analyze_conversation_context(conversation_history or [], user_message)
        
        # Получаем конфигурацию ответа
        response_config = get_response_config(emotion_type, context_type)
        
        # Загружаем базовый системный промпт
        base_system_prompt = load_system_prompt()
        
        # Добавляем инструкции по стилю ответа
        style_instructions = get_style_instructions(response_config["style"])
        
        # Формируем расширенный системный промпт
        enhanced_system_prompt = f"""{base_system_prompt}

ИНСТРУКЦИИ ПО ДЛИНЕ И СТИЛЮ ОТВЕТА:
{style_instructions}

Текущая ситуация: {response_config["description"]}
Рекомендуемое количество предложений: {response_config["min_sentences"]}-{response_config["max_sentences"]}
"""
        
        # Формируем сообщения для API
        messages = [{"role": "system", "content": enhanced_system_prompt}]
        
        # Добавляем историю разговора, если есть
        if conversation_history:
            messages.extend(conversation_history)
        
        # Добавляем текущее сообщение пользователя
        messages.append({"role": "user", "content": user_message})
        
        # Отправляем запрос к GPT с динамическими параметрами
        response = client.chat.completions.create(
            model=OpenAIConfig.MODEL,
            messages=messages,
            max_tokens=response_config["max_tokens"],
            temperature=OpenAIConfig.TEMPERATURE
        )
        
        # Логируем конфигурацию для отладки
        print(f"🎯 Динамический ответ: {emotion_type} + {context_type} = {response_config['max_tokens']} токенов")
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Ошибка при обращении к GPT: {e}")
        return "Извини, у меня сейчас технические проблемы. Попробуй чуть позже 🤖"

def close_openai_client():
    """Закрывает клиент OpenAI"""
    global _openai_client
    if _openai_client:
        try:
            # OpenAI клиент не требует явного закрытия
            pass
        except Exception as e:
            print(f"Ошибка при закрытии OpenAI клиента: {e}")
        finally:
            _openai_client = None