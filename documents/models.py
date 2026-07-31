"""Модель документа и состояния процесса административной модерации."""

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

from documents.validators import validate_file_size


class Document(models.Model):
    """Хранить файл, владельца, статус и результат проверки документа."""

    class Status(models.TextChoices):
        """Допустимые состояния документа в процессе модерации."""

        PENDING = "pending", "Ожидает проверки"
        APPROVED = "approved", "Подтвержден"
        REJECTED = "rejected", "Отклонен"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Владелец",
    )
    title = models.CharField(max_length=255, verbose_name="Название")
    file = models.FileField(
        upload_to="documents/%Y/%m/%d/",
        validators=[
            FileExtensionValidator(settings.ALLOWED_DOCUMENT_EXTENSIONS),
            validate_file_size,
        ],
        verbose_name="Файл",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="Статус",
    )
    rejection_reason = models.TextField(blank=True, verbose_name="Причина отклонения")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_documents",
        verbose_name="Проверил",
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата проверки",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата изменения")

    class Meta:
        """Настроить сортировку, человекочитаемые имена и индекс выборки."""

        ordering = ("-created_at",)
        verbose_name = "Документ"
        verbose_name_plural = "Документы"
        indexes = [
            models.Index(fields=("owner", "status"), name="doc_owner_status_idx")
        ]

    def __str__(self) -> str:
        """Вернуть название документа и его текущий статус."""
        return f"{self.title} — {self.get_status_display()}"
