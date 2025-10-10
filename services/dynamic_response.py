#!/usr/bin/env python3
"""
Модуль для динамического определения длины ответов в зависимости от контекста и эмоций
"""

from typing import Dict, Tuple

class DynamicResponseConfig:
    """
    Конфигурация для динамических ответов в зависимости от эмоционального состояния
    """
    
    # Базовые настройки длины ответов для разных типов эмоций
    EMOTION_RESPONSE_CONFIG = {
        # Критические ситуации - требуют развернутых, поддерживающих ответов
        "sos": {
            "max_tokens": 2000,
            "min_sentences": 6,
            "max_sentences": 12,
            "style": "supportive_detailed",
            "description": "Суицидальные мысли, угроза жизни - максимальная поддержка"
        },
        
        # Сильные негативные эмоции - нужны развернутые ответы с эмпатией
        "anger": {
            "max_tokens": 1500,
            "min_sentences": 4,
            "max_sentences": 8,
            "style": "empathetic_detailed",
            "description": "Злость, ярость - развернутая эмпатия и понимание"
        },
        
        "sadness": {
            "max_tokens": 1500,
            "min_sentences": 4,
            "max_sentences": 8,
            "style": "comforting_detailed",
            "description": "Грусть, печаль - утешение и поддержка"
        },
        
        "tired": {
            "max_tokens": 1200,
            "min_sentences": 3,
            "max_sentences": 6,
            "style": "gentle_understanding",
            "description": "Усталость, выгорание - мягкое понимание"
        },
        
        # Провокации - краткие, но четкие границы
        "provocation": {
            "max_tokens": 800,
            "min_sentences": 2,
            "max_sentences": 4,
            "style": "firm_boundaries",
            "description": "Провокации - четкие границы, но без агрессии"
        },
        
        # Обычные эмоциональные темы - средняя длина
        "generic": {
            "max_tokens": 1000,
            "min_sentences": 3,
            "max_sentences": 5,
            "style": "warm_engaging",
            "description": "Общие эмоциональные темы - теплое общение"
        },
        
        # Нейтральные темы - короткие ответы
        "neutral": {
            "max_tokens": 600,
            "min_sentences": 1,
            "max_sentences": 3,
            "style": "friendly_concise",
            "description": "Нейтральные темы - дружелюбно и кратко"
        }
    }
    
    # Модификаторы длины в зависимости от контекста разговора
    CONTEXT_MODIFIERS = {
        "first_message": 1.3,      # Первое сообщение - чуть длиннее для знакомства
        "follow_up": 1.0,          # Обычное продолжение
        "deep_conversation": 1.4,   # Глубокий разговор - более развернуто
        "quick_exchange": 0.8,     # Быстрый обмен - короче
        "complex_topic": 1.5,      # Сложная тема - подробнее
        "simple_question": 0.7     # Простой вопрос - кратко
    }

def get_response_config(emotion_type: str, context_type: str = "follow_up") -> Dict:
    """
    Получает конфигурацию ответа в зависимости от эмоции и контекста
    
    Args:
        emotion_type: Тип эмоции (sos, anger, sadness, etc.)
        context_type: Тип контекста разговора
    
    Returns:
        Dict с параметрами для генерации ответа
    """
    # Получаем базовую конфигурацию для эмоции
    base_config = DynamicResponseConfig.EMOTION_RESPONSE_CONFIG.get(
        emotion_type, 
        DynamicResponseConfig.EMOTION_RESPONSE_CONFIG["neutral"]
    )
    
    # Получаем модификатор контекста
    context_modifier = DynamicResponseConfig.CONTEXT_MODIFIERS.get(context_type, 1.0)
    
    # Применяем модификатор к max_tokens
    adjusted_max_tokens = int(base_config["max_tokens"] * context_modifier)
    
    # Ограничиваем минимум и максимум
    adjusted_max_tokens = max(300, min(2500, adjusted_max_tokens))
    
    return {
        "max_tokens": adjusted_max_tokens,
        "min_sentences": base_config["min_sentences"],
        "max_sentences": base_config["max_sentences"],
        "style": base_config["style"],
        "description": base_config["description"],
        "emotion_type": emotion_type,
        "context_type": context_type,
        "context_modifier": context_modifier
    }

def analyze_conversation_context(conversation_history: list, current_message: str) -> str:
    """
    Анализирует контекст разговора для определения типа контекста
    
    Args:
        conversation_history: История сообщений
        current_message: Текущее сообщение
    
    Returns:
        Тип контекста разговора
    """
    if not conversation_history:
        return "first_message"
    
    # Анализируем длину истории
    history_length = len(conversation_history)
    
    # Анализируем текущее сообщение
    message_length = len(current_message.split())
    current_lower = current_message.lower()
    
    # Простые вопросы
    simple_questions = ["как дела", "что делаешь", "как ты", "привет", "пока", "спасибо"]
    if any(q in current_lower for q in simple_questions) and message_length <= 5:
        return "simple_question"
    
    # Сложные темы (длинные сообщения с вопросами)
    if message_length > 20 or "?" in current_message:
        return "complex_topic"
    
    # Глубокий разговор (много сообщений в истории)
    if history_length > 10:
        return "deep_conversation"
    
    # Быстрый обмен (короткие сообщения)
    if message_length <= 3:
        return "quick_exchange"
    
    return "follow_up"

def get_style_instructions(style: str) -> str:
    """
    Возвращает инструкции по стилю ответа для системного промпта
    
    Args:
        style: Стиль ответа
    
    Returns:
        Текстовые инструкции для промпта
    """
    style_instructions = {
        "supportive_detailed": """
        Отвечай развернуто и поддерживающе. Покажи глубокое понимание и заботу.
        Предложи конкретную помощь. Используй 6-12 предложений.
        Будь максимально эмпатичным и внимательным к деталям.
        """,
        
        "empathetic_detailed": """
        Отвечай с глубокой эмпатией и пониманием. Признай чувства человека.
        Предложи способы справиться с ситуацией. Используй 4-8 предложений.
        Покажи, что понимаешь причины злости и готов выслушать.
        """,
        
        "comforting_detailed": """
        Отвечай тепло и утешающе. Окажи эмоциональную поддержку.
        Помоги увидеть перспективу. Используй 4-8 предложений.
        Будь мягким, но не банальным в утешении.
        """,
        
        "gentle_understanding": """
        Отвечай мягко и с пониманием усталости. Не требуй активности.
        Предложи отдых или простые решения. Используй 3-6 предложений.
        Покажи, что понимаешь состояние истощения.
        """,
        
        "firm_boundaries": """
        Отвечай спокойно, но четко обозначь границы. Не поддавайся на провокации.
        Перенаправь на конструктивное общение. Используй 2-4 предложения.
        Будь вежливым, но твердым.
        """,
        
        "warm_engaging": """
        Отвечай тепло и вовлекающе. Поддержи разговор.
        Задай уточняющие вопросы. Используй 3-5 предложений.
        Покажи искренний интерес к теме.
        """,
        
        "friendly_concise": """
        Отвечай дружелюбно и кратко. Будь полезным, но не многословным.
        Используй 1-3 предложения. Отвечай по существу с теплотой.
        """
    }
    
    return style_instructions.get(style, style_instructions["friendly_concise"]).strip()

def format_response_config_info(config: Dict) -> str:
    """
    Форматирует информацию о конфигурации ответа для отладки
    
    Args:
        config: Конфигурация ответа
    
    Returns:
        Отформатированная строка с информацией
    """
    return f"""
🎯 Конфигурация ответа:
   Эмоция: {config['emotion_type']} 
   Контекст: {config['context_type']}
   Max tokens: {config['max_tokens']}
   Предложения: {config['min_sentences']}-{config['max_sentences']}
   Стиль: {config['style']}
   Модификатор: {config['context_modifier']}
   Описание: {config['description']}
    """.strip()