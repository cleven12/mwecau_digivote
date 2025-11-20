# src/backend/mw_es/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mw_es.settings")
app = Celery("mw_es")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()