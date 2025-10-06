# Логика записи дневника

from datetime import datetime

def create_journal_entry(mood: int, facts: str, gratitude: str, plan: str) -> dict:
    """
    Создает запись дневника.
    :param mood: Настроение от 0 до 10.
    :param facts: Факты дня.
    :param gratitude: За что благодарен.
    :param plan: План на день.
    :return: Словарь с записью дневника.
    """
    return {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mood": mood,
        "facts": facts,
        "gratitude": gratitude,
        "plan": plan
    }