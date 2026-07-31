"""Конфигурация приложения документов."""

from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    """Задать параметры приложения загрузки и модерации документов."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "documents"
