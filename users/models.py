"""Пользовательская модель с обязательным уникальным адресом электронной почты."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Расширить стандартного пользователя уникальным полем email."""

    email = models.EmailField("Электронная почта", unique=True)

    REQUIRED_FIELDS = ["email"]

    def __str__(self) -> str:
        """Вернуть email для отображения пользователя в интерфейсе администратора."""
        return self.email
