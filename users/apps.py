"""Конфигурация приложения пользователей."""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Задать параметры приложения с пользовательской моделью."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
