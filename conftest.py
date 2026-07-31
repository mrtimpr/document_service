"""Общие pytest-фикстуры для тестирования пользователей и документов."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture(autouse=True)
def temporary_media_root(settings, tmp_path):
    """Изолировать тестовые файлы во временном каталоге."""
    settings.MEDIA_ROOT = tmp_path / "media"


@pytest.fixture
def user(db):
    """Создать обычного пользователя для тестов API."""
    return User.objects.create_user(
        username="user",
        email="user@example.com",
        password="StrongPass123!",
    )


@pytest.fixture
def second_user(db):
    """Создать второго пользователя для проверки изоляции данных."""
    return User.objects.create_user(
        username="second",
        email="second@example.com",
        password="StrongPass123!",
    )


@pytest.fixture
def admin_user(db):
    """Создать администратора для тестов модерации."""
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="StrongPass123!",
    )


@pytest.fixture
def api_client():
    """Вернуть неавторизованный тестовый клиент DRF."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Вернуть тестовый клиент, авторизованный как обычный пользователь."""
    api_client.force_authenticate(user=user)
    return api_client
