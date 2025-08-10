import os 
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('stock_alert_system')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# استخدام Django Database Scheduler
app.conf.beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'