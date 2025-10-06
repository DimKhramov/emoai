# Логика определения намерений

def determine_intent(message: str) -> str:
    """
    Определяет намерение пользователя на основе ключевых слов.
    Возможные намерения: talk, coach, facts, journal, sos.
    """
    message_lower = message.lower()

    if any(word in message_lower for word in ["паника", "не хочу жить", "самоуб"]):
        return "sos"
    elif any(word in message_lower for word in ["дневник", "запись"]):
        return "journal"
    elif any(word in message_lower for word in ["факт", "шаг", "инструкция"]):
        return "facts"
    elif any(word in message_lower for word in ["помощь", "вопрос", "структура"]):
        return "coach"
    else:
        return "talk"