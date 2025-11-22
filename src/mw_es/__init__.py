"""
MWECAU Election Platform - Django Project Initialization
"""
from .celery_app import app as celery_app

__all__ = ('celery_app',)
