"""Тесты регистрации пользователей через REST API."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

User = get_user_model()

pytestmark = pytest.mark.django_db


def test_registration(api_client):
    response = api_client.post(
        reverse("register"),
        {
            "username": "new-user",
            "email": "new@example.com",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    user = User.objects.get(username="new-user")
    assert user.email == "new@example.com"
    assert user.check_password("StrongPass123!")
    assert "password" not in response.data


def test_email_must_be_unique(api_client, user):
    response = api_client.post(
        reverse("register"),
        {
            "username": "another-user",
            "email": user.email,
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data
