"""Пользовательские валидаторы загружаемых документов."""

from typing import Protocol

from django.conf import settings
from django.core.exceptions import ValidationError


class SizedFile(Protocol):
    """Описать минимальный интерфейс файла, используемый валидатором."""

    size: int


def validate_file_size(file: SizedFile) -> None:
    """Отклонить файл, размер которого превышает установленный лимит."""
    max_size = settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024
    if file.size > max_size:
        raise ValidationError(
            f"Размер файла не должен превышать {settings.MAX_DOCUMENT_SIZE_MB} МБ."
        )
