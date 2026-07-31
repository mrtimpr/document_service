"""Маршруты приложения пользователей."""

from django.urls import path

from users.views import RegistrationView

urlpatterns = [
    path("", RegistrationView.as_view(), name="register"),
]
