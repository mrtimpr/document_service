"""Настройка пользовательской модели в Django Admin."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Настроить список, поиск и стандартные формы управления пользователями."""

    list_display = ("username", "email", "is_staff", "is_active")
    search_fields = ("username", "email")
