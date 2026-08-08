"""Сериализаторы регистрации пользователей через REST API."""

from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    """Проверить регистрационные данные и безопасно сохранить пароль."""

    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        """Описать поля API регистрации."""

        model = User
        fields = ("id", "username", "email", "password")
        read_only_fields = ("id",)

    def create(self, validated_data: dict[str, Any]):
        """Создать пользователя через менеджер с хешированием пароля."""
        return User.objects.create_user(**validated_data)
