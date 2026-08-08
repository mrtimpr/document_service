"""Сериализаторы загрузки и безопасного представления документов."""

from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.urls import reverse
from rest_framework import serializers

from documents.models import Document
from documents.validators import validate_file_size


class DocumentSerializer(serializers.ModelSerializer):
    """Вернуть метаданные документа без раскрытия прямого пути к файлу."""

    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    reviewed_by_email = serializers.EmailField(
        source="reviewed_by.email",
        read_only=True,
        allow_null=True,
    )
    file_name = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        """Разрешить только чтение системных данных документа."""

        model = Document
        fields = (
            "id",
            "title",
            "file_name",
            "download_url",
            "status",
            "rejection_reason",
            "owner_email",
            "reviewed_by_email",
            "reviewed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_file_name(self, obj: Document) -> str:
        """Вернуть безопасное имя файла без каталога хранения."""
        return Path(obj.file.name).name

    def get_download_url(self, obj: Document) -> str:
        """Сформировать URL защищенного скачивания документа."""
        url = reverse("document-download", args=[obj.pk])
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url


class DocumentCreateSerializer(serializers.ModelSerializer):
    """Проверить файл и создать документ с системным статусом pending."""

    # Явно сохраняем валидаторы модели, так как поле переопределено в сериализаторе.
    file = serializers.FileField(
        write_only=True,
        validators=[
            FileExtensionValidator(settings.ALLOWED_DOCUMENT_EXTENSIONS),
            validate_file_size,
        ],
    )

    class Meta:
        """Ограничить входные поля названием и содержимым файла."""

        model = Document
        fields = ("id", "title", "file", "status", "created_at")
        read_only_fields = ("id", "status", "created_at")

    def validate_file(self, file: Any):
        """Отклонить файл с MIME-типом, отсутствующим в белом списке."""
        content_type = getattr(file, "content_type", None)
        if content_type and content_type not in settings.ALLOWED_DOCUMENT_CONTENT_TYPES:
            raise serializers.ValidationError("Недопустимый MIME-тип файла.")
        return file
