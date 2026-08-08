"""Интеграционные тесты JWT, OpenAPI, Swagger и ReDoc."""

import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


def test_jwt_token_endpoint_returns_token_pair(api_client, user):
    response = api_client.post(
        reverse("token_obtain_pair"),
        {"username": user.username, "password": "StrongPass123!"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data


def test_openapi_schema_is_available_without_authentication(api_client):
    response = api_client.get(reverse("schema"))

    assert response.status_code == status.HTTP_200_OK


def test_swagger_is_available_without_authentication(api_client):
    response = api_client.get(reverse("swagger-ui"))

    assert response.status_code == status.HTTP_200_OK
    assert b"swagger" in response.content.lower()


def test_redoc_is_available_without_authentication(api_client):
    response = api_client.get(reverse("redoc"))

    assert response.status_code == status.HTTP_200_OK
    assert b"redoc" in response.content.lower()
