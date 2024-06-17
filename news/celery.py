from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Установите переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsportal.settings')

# Создайте экземпляр Celery
app = Celery('news')

# Загружаем настройки из файла settings.py с префиксом 'CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживаем задачи в модуле utils
app.autodiscover_tasks(['news'])

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
