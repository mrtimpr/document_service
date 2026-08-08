"""Инициализация Django-проекта и экспорт приложения Celery."""

from config.celery import app as celery_app

__all__ = ("celery_app",)
