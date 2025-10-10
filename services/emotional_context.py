"""
Модуль для анализа эмоционального контекста и предотвращения повторных вопросов
"""

import re
from typing import List, Dict, Optional
from services.intents import determine_intent, analyze_emotional_state, get_response_tone


def analyze_conversation_context(history: List[Dict]) -> Dict:
    """
    Анализирует контекст разговора для предотвращения повторных вопросов
    и определения эмоционального состояния
    """
    if not history:
        return {
            'recent_questions': [],
            'emotional_state': 'neutral',
            'topics_discussed': [],
            'user_responses': {},
            'conversation_flow': 'new'
        }
    
    recent_questions = []
    topics_discussed = []
    user_responses = {}
    emotional_indicators = []
    
    # Анализируем последние 5 сообщений
    recent_messages = history[-5:] if len(history) >= 5 else history
    
    for i, msg in enumerate(recent_messages):
        content = msg.get('content', '').lower()
        role = msg.get('role', '')
        
        # Собираем вопросы от ассистента
        if role == 'assistant' and ('?' in content or 
                                   any(q in content for q in ['что', 'как', 'почему', 'когда', 'где', 'кто'])):
            recent_questions.append({
                'question': content,
                'position': i,
                'answered': False
            })
        
        # Проверяем ответы пользователя на вопросы
        if role == 'user' and recent_questions:
            # Ищем последний неотвеченный вопрос
            for q in reversed(recent_questions):
                if not q['answered'] and i > q['position']:
                    q['answered'] = True
                    user_responses[q['question']] = content
                    
                    # Специальная обработка коротких ответов
                    if len(content.strip()) <= 3:  # Короткие ответы типа "да", "нет", "не"
                        # Определяем тип короткого ответа
                        short_answer_type = classify_short_answer(content.strip())
                        user_responses[q['question']] = {
                            'content': content,
                            'type': short_answer_type,
                            'is_short': True
                        }
                    break
        
        # Анализируем эмоциональные индикаторы
        if role == 'user':
            emotional_state = analyze_emotional_state(content)
            if emotional_state != 'neutral':
                emotional_indicators.append(emotional_state)
            
            # Определяем обсуждаемые темы
            topics = extract_topics(content)
            topics_discussed.extend(topics)
    
    # Определяем общее эмоциональное состояние
    if emotional_indicators:
        # Приоритет отдаем последним эмоциям
        current_emotional_state = emotional_indicators[-1]
    else:
        current_emotional_state = 'neutral'
    
    # Определяем поток разговора
    conversation_flow = determine_conversation_flow(recent_messages)
    
    return {
        'recent_questions': recent_questions,
        'emotional_state': current_emotional_state,
        'topics_discussed': list(set(topics_discussed)),
        'user_responses': user_responses,
        'conversation_flow': conversation_flow,
        'unanswered_questions': [q for q in recent_questions if not q['answered']]
    }


def classify_short_answer(answer: str) -> str:
    """
    Классифицирует короткие ответы пользователя
    """
    answer_lower = answer.lower().strip()
    
    # Отрицательные ответы
    negative_answers = ['нет', 'не', 'неа', 'нее', 'не-а', 'не-е']
    if answer_lower in negative_answers:
        return 'negative'
    
    # Положительные ответы
    positive_answers = ['да', 'ага', 'угу', 'конечно', 'да-да', 'ок', 'хорошо']
    if answer_lower in positive_answers:
        return 'positive'
    
    # Неопределенные ответы
    uncertain_answers = ['хз', 'не знаю', 'незнаю', 'хм', 'эм', 'ну']
    if answer_lower in uncertain_answers:
        return 'uncertain'
    
    # Если не удалось классифицировать
    return 'unclear'


def extract_topics(text: str) -> List[str]:
    """Извлекает основные темы из текста"""
    topics = []
    text_lower = text.lower()
    
    # Словарь тем и их ключевых слов
    topic_keywords = {
        'работа': ['работа', 'работать', 'офис', 'коллеги', 'начальник', 'проект', 'карьера'],
        'отношения': ['отношения', 'парень', 'девушка', 'муж', 'жена', 'любовь', 'ссора', 'расставание'],
        'семья': ['семья', 'родители', 'мама', 'папа', 'дети', 'ребенок', 'брат', 'сестра'],
        'здоровье': ['здоровье', 'болеть', 'врач', 'лечение', 'болезнь', 'самочувствие'],
        'учеба': ['учеба', 'университет', 'экзамен', 'студент', 'преподаватель', 'диплом'],
        'хобби': ['хобби', 'увлечение', 'спорт', 'музыка', 'книги', 'фильмы', 'игры'],
        'планы': ['планы', 'цели', 'мечты', 'будущее', 'хочу', 'планирую']
    }
    
    for topic, keywords in topic_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            topics.append(topic)
    
    return topics


def determine_conversation_flow(messages: List[Dict]) -> str:
    """Определяет характер течения разговора"""
    if len(messages) < 2:
        return 'new'
    
    user_messages = [msg for msg in messages if msg.get('role') == 'user']
    
    if not user_messages:
        return 'new'
    
    last_user_msg = user_messages[-1].get('content', '').lower()
    
    # Проверяем признаки раздражения или усталости от повторов
    irritation_signs = [
        'уже говорил', 'уже сказал', 'повторяешь', 'опять спрашиваешь',
        'я же ответил', 'не спрашивай снова', 'хватит', 'достаточно'
    ]
    
    if any(sign in last_user_msg for sign in irritation_signs):
        return 'irritated'
    
    # Проверяем глубину разговора
    if len(user_messages) > 3:
        return 'deep'
    
    return 'developing'


def should_avoid_question(context: Dict, potential_question: str) -> bool:
    """
    Определяет, стоит ли избегать задавания вопроса на основе контекста
    """
    # Проверяем, не задавали ли похожий вопрос недавно
    recent_questions = context.get('recent_questions', [])
    potential_lower = potential_question.lower()
    
    similar_questions_count = 0
    for q in recent_questions:
        question_lower = q['question'].lower()
        # Проверяем схожесть вопросов
        similarity = calculate_question_similarity(potential_lower, question_lower)
        if similarity > 0.6:  # Понижаем порог для более строгой проверки
            similar_questions_count += 1
    
    # Если уже было 2 или больше похожих вопросов - избегаем повтора
    if similar_questions_count >= 2:
        return True
    
    # Если пользователь раздражен повторами
    if context.get('conversation_flow') == 'irritated':
        return True
    
    # Если есть неотвеченные вопросы
    if context.get('unanswered_questions'):
        return True
    
    # Дополнительная проверка: если последние 2 вопроса очень похожи
    if len(recent_questions) >= 2:
        last_two = recent_questions[-2:]
        if all(calculate_question_similarity(potential_lower, q['question'].lower()) > 0.7 for q in last_two):
            return True
    
    return False


def calculate_question_similarity(q1: str, q2: str) -> float:
    """Вычисляет схожесть двух вопросов"""
    # Простая проверка на основе ключевых слов
    q1_words = set(q1.split())
    q2_words = set(q2.split())
    
    if not q1_words or not q2_words:
        return 0.0
    
    intersection = q1_words.intersection(q2_words)
    union = q1_words.union(q2_words)
    
    return len(intersection) / len(union)


def get_context_aware_prompt_addition(context: Dict) -> str:
    """
    Генерирует дополнение к промпту на основе контекста разговора
    """
    additions = []
    
    # Проверяем короткие ответы пользователя
    user_responses = context.get('user_responses', {})
    short_responses = []
    for question, response in user_responses.items():
        if isinstance(response, dict) and response.get('is_short'):
            short_responses.append(response)
    
    if short_responses:
        latest_short = short_responses[-1]
        response_type = latest_short.get('type', 'unclear')
        
        if response_type == 'negative':
            additions.append("ВАЖНО: Пользователь дал отрицательный ответ на твой вопрос. Не настаивай на теме, переключись на что-то другое или предложи поддержку.")
        elif response_type == 'positive':
            additions.append("Пользователь согласился или подтвердил. Можешь развить тему дальше.")
        elif response_type == 'uncertain':
            additions.append("Пользователь не уверен или не знает. Предложи помощь в размышлениях или смени тему.")
        elif response_type == 'unclear':
            additions.append("Пользователь дал неясный короткий ответ. Попроси уточнения мягко или переключись на другую тему.")
    
    # Проверяем повторяющиеся вопросы
    recent_questions = context.get('recent_questions', [])
    if len(recent_questions) >= 2:
        # Проверяем схожесть последних вопросов
        similar_count = 0
        for i in range(len(recent_questions)):
            for j in range(i + 1, len(recent_questions)):
                similarity = calculate_question_similarity(
                    recent_questions[i]['question'].lower(),
                    recent_questions[j]['question'].lower()
                )
                if similarity > 0.6:
                    similar_count += 1
        
        if similar_count >= 1:
            additions.append("⚠️ КРИТИЧЕСКИ ВАЖНО: Ты уже задавал похожие вопросы! НЕ ПОВТОРЯЙ вопросы типа 'Как дела?', 'Как у тебя дела?' и подобные. Вместо этого развивай тему, делись чем-то интересным или предлагай активность.")
    
    # Если есть неотвеченные вопросы
    if context.get('unanswered_questions'):
        additions.append("ВАЖНО: Ты уже задавал вопросы, на которые пользователь не ответил. Не задавай новых вопросов, а развивай тему или переходи к поддержке.")
    
    # Если пользователь раздражен
    if context.get('conversation_flow') == 'irritated':
        additions.append("ВНИМАНИЕ: Пользователь показывает признаки раздражения от повторов. Будь более внимательным к его ответам и не повторяй вопросы.")
    
    # Эмоциональное состояние
    emotional_state = context.get('emotional_state', 'neutral')
    if emotional_state == 'negative':
        additions.append("Пользователь в негативном эмоциональном состоянии. Приоритет - поддержка и эмпатия.")
    elif emotional_state == 'positive':
        additions.append("Пользователь в хорошем настроении. Поддержи позитивную атмосферу.")
    
    # Обсуждаемые темы
    topics = context.get('topics_discussed', [])
    if topics:
        topics_str = ', '.join(topics)
        additions.append(f"В разговоре уже обсуждались темы: {topics_str}. Учитывай это в ответе.")
    
    return '\n'.join(additions) if additions else ""


def format_context_for_gpt(history: List[Dict], current_message: str) -> tuple:
    """
    Форматирует контекст для отправки в GPT с учетом эмоционального анализа
    """
    # Анализируем контекст
    context = analyze_conversation_context(history)
    
    # Определяем интент текущего сообщения
    intent = determine_intent(current_message)
    
    # Получаем тон ответа
    response_tone = get_response_tone(intent)
    
    # Формируем дополнение к промпту
    context_addition = get_context_aware_prompt_addition(context)
    
    return context, intent, response_tone, context_addition