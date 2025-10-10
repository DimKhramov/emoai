# Логика определения намерений

def determine_intent(message: str) -> str:
    """
    Определяет намерение пользователя на основе ключевых слов и эмоционального контекста.
    Возможные намерения: support, advice, question, chat, greeting, goodbye, gratitude, compliment, sos.
    """
    message_lower = message.lower()

    # Критические ситуации - высший приоритет
    if any(word in message_lower for word in ["паника", "не хочу жить", "самоуб", "покончить с собой", "умереть"]):
        return "sos"
    
    # Эмоциональная поддержка - новый приоритетный интент
    elif any(word in message_lower for word in [
        "плохо", "тяжело", "устал", "устала", "больно", "одиноко", "грустно", "депрессия",
        "тревожно", "страшно", "не могу", "не получается", "расстроен", "расстроена",
        "злой", "злая", "раздражает", "бесит", "надоело", "достало", "сил нет",
        "проблемы", "беда", "кошмар", "ужас", "паршиво", "отвратительно"
    ]):
        return "support"
    
    # Запрос совета или помощи
    elif any(phrase in message_lower for phrase in [
        "что делать", "как быть", "посоветуй", "помоги", "не знаю что делать",
        "как поступить", "что выбрать", "как решить", "подскажи", "нужна помощь",
        "как лучше", "стоит ли", "правильно ли"
    ]):
        return "advice"
    
    # Вопросы (фактические или информационные)
    elif (message_lower.endswith("?") or 
          any(word in message_lower for word in [
              "почему", "зачем", "как", "где", "когда", "кто", "что такое",
              "объясни", "расскажи", "что значит", "в чем разница"
          ])):
        return "question"
    
    # Простые социальные интенты
    elif any(word in message_lower for word in ["привет", "здравствуй", "добро утро", "добрый день", "добрый вечер", "хай", "hi", "hello"]):
        return "greeting"
    elif any(word in message_lower for word in ["пока", "до свидания", "увидимся", "прощай", "bye", "goodbye"]):
        return "goodbye"
    elif any(word in message_lower for word in ["спасибо", "благодарю", "спс", "thanks", "thank you"]):
        return "gratitude"
    elif any(word in message_lower for word in ["молодец", "хорошо", "отлично", "супер", "круто", "классно"]):
        return "compliment"
    
    # Все остальное - обычный чат
    else:
        return "chat"


def get_response_tone(intent: str) -> str:
    """
    Возвращает рекомендуемый тон ответа для каждого типа намерения.
    """
    tone_mapping = {
        "support": "empathetic",      # Эмпатичный, поддерживающий
        "advice": "helpful",          # Полезный, направляющий
        "question": "informative",    # Информативный, четкий
        "chat": "friendly",           # Дружелюбный, легкий
        "greeting": "warm",           # Теплый, приветливый
        "goodbye": "warm",            # Теплый, прощальный
        "gratitude": "appreciative",  # Благодарный, скромный
        "compliment": "modest",       # Скромный, благодарный
        "sos": "crisis"              # Кризисный, направляющий к помощи
    }
    return tone_mapping.get(intent, "friendly")


def analyze_emotional_state(message: str) -> str:
    """
    Анализирует эмоциональное состояние пользователя из сообщения.
    Возвращает строку с основным эмоциональным состоянием.
    """
    message_lower = message.lower()
    
    emotional_indicators = {
        "negative": ["плохо", "тяжело", "грустно", "больно", "злой", "раздражает", "устал"],
        "positive": ["хорошо", "отлично", "радостно", "счастлив", "весело", "круто"],
        "neutral": ["нормально", "обычно", "так себе", "ничего особенного"],
        "anxious": ["тревожно", "волнуюсь", "переживаю", "боюсь", "страшно"],
        "frustrated": ["бесит", "достало", "надоело", "раздражает", "злой"]
    }
    
    # Проверяем на наличие эмоциональных индикаторов
    for emotion, keywords in emotional_indicators.items():
        if any(keyword in message_lower for keyword in keywords):
            return emotion
    
    # Если эмоциональных индикаторов не найдено, возвращаем neutral
    return "neutral"