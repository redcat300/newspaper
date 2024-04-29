from django import template
import re

register = template.Library()

@register.filter(name='censor')
def censor(value):
    # Список нежелательных слов, которые будем цензурировать
    unwanted_words = ['bad_word1', 'bad_word2', 'bad_word3']  # Замените на реальные слова

    # Регулярное выражение для поиска слов из списка нежелательных слов
    regex = re.compile(r'\b(' + '|'.join(map(re.escape, unwanted_words)) + r')\b', re.IGNORECASE)

    # Заменяем нежелательные слова на символ '*'
    return regex.sub(lambda x: '*' * len(x.group()), value)
