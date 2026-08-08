"""Представления API регистрации пользователей."""

from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions

from users.serializers import RegistrationSerializer


@extend_schema(tags=["Authentication"])
class RegistrationView(generics.CreateAPIView):
    """Зарегистрировать нового пользователя без предварительной авторизации."""

    serializer_class = RegistrationSerializer
    permission_classes = (permissions.AllowAny,)
