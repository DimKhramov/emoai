"""
Модуль для фильтрации неподходящего контента
"""

import re
from typing import Dict, List, Tuple

class ContentFilter:
    """
    Фильтр контента для блокировки неподходящих тем
    """
    
    # Список запрещенных тем и ключевых слов
    INAPPROPRIATE_TOPICS = {
        "sexual_content": {
            "keywords": [
                "анальный секс", "анал", "оральный секс", "секс", "интимность", 
                "половой акт", "мастурбация", "порно", "эротика", "интим",
                "презерватив", "смазка", "возбуждение", "оргазм", "либидо"
            ],
            "patterns": [
                r"\b(секс|интим)\w*",
                r"\b(половой|сексуальн)\w*",
                r"\b(эротич|порн)\w*"
            ],
            "response": "Я понимаю, что у тебя могут быть разные вопросы, но я создан для эмоциональной поддержки и дружеского общения. Для вопросов интимного характера лучше обратиться к специалистам или проверенным медицинским источникам. 😊\n\nДавай лучше поговорим о том, как дела? Что тебя сейчас волнует?"
        },
        
        "violence": {
            "keywords": [
                "убить", "убийство", "насилие", "избить", "драка", "война",
                "оружие", "нож", "пистолет", "кровь", "смерть"
            ],
            "patterns": [
                r"\b(убь|убив)\w*",
                r"\b(насил|избив)\w*",
                r"\b(оруж|нож|пистол)\w*"
            ],
            "response": "Я вижу, что тема довольно тяжелая. Если тебе нужна помощь или поддержка в сложной ситуации, я здесь. Но давай найдем более конструктивный способ обсудить то, что тебя беспокоит. 💙\n\nЧто на самом деле происходит? Чем могу помочь?"
        },
        
        "drugs": {
            "keywords": [
                "наркотики", "кокаин", "героин", "марихуана", "амфетамин",
                "экстази", "лсд", "спайс", "соль", "дозу", "укол"
            ],
            "patterns": [
                r"\b(наркот|дозу|укол)\w*",
                r"\b(кокаин|героин|марихуан)\w*"
            ],
            "response": "Понимаю, что могут быть разные жизненные ситуации. Если тебе нужна помощь или поддержка, я рядом. Но для серьезных вопросов лучше обратиться к специалистам. 🌿\n\nРасскажи, что тебя сейчас беспокоит? Как дела в целом?"
        }
    }
    
    @classmethod
    def check_content(cls, message: str) -> Tuple[bool, str, str]:
        """
        Проверяет сообщение на неподходящий контент
        
        Args:
            message: Текст сообщения для проверки
            
        Returns:
            Tuple[bool, str, str]: (is_inappropriate, topic_type, suggested_response)
        """
        message_lower = message.lower()
        
        for topic_type, topic_data in cls.INAPPROPRIATE_TOPICS.items():
            # Проверяем ключевые слова
            for keyword in topic_data["keywords"]:
                if keyword.lower() in message_lower:
                    return True, topic_type, topic_data["response"]
            
            # Проверяем регулярные выражения
            for pattern in topic_data["patterns"]:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    return True, topic_type, topic_data["response"]
        
        return False, "", ""
    
    @classmethod
    def is_question_about_inappropriate_topic(cls, message: str) -> bool:
        """
        Проверяет, является ли сообщение вопросом о неподходящей теме
        
        Args:
            message: Текст сообщения
            
        Returns:
            bool: True если это вопрос о неподходящей теме
        """
        question_indicators = ["?", "как", "что", "где", "когда", "почему", "зачем", "расскажи", "объясни"]
        message_lower = message.lower()
        
        # Проверяем, есть ли индикаторы вопроса
        has_question = any(indicator in message_lower for indicator in question_indicators)
        
        if has_question:
            is_inappropriate, _, _ = cls.check_content(message)
            return is_inappropriate
        
        return False
    
    @classmethod
    def get_safe_response_for_topic(cls, topic_type: str) -> str:
        """
        Возвращает безопасный ответ для конкретной темы
        
        Args:
            topic_type: Тип неподходящей темы
            
        Returns:
            str: Безопасный ответ
        """
        if topic_type in cls.INAPPROPRIATE_TOPICS:
            return cls.INAPPROPRIATE_TOPICS[topic_type]["response"]
        
        # Общий безопасный ответ
        return """Понимаю, что у тебя могут быть разные вопросы, но я создан для эмоциональной поддержки и дружеского общения. 😊

Давай лучше поговорим о том, как у тебя дела? Что тебя сейчас волнует или радует?"""