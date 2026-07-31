"""Сервисный слой атомарной модерации документов."""

from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from documents.models import Document
from documents.tasks import notify_user_about_document_status


@transaction.atomic
def moderate_document(
    *,
    document: Document,
    status: str,
    reviewer: Any,
    rejection_reason: str = "",
) -> Document:
    """Атомарно подтвердить или отклонить документ и поставить письмо в очередь."""
    if status not in {Document.Status.APPROVED, Document.Status.REJECTED}:
        raise ValidationError("Недопустимый итоговый статус документа.")

    # Блокировка строки исключает одновременную обработку двумя администраторами.
    locked = Document.objects.select_for_update().get(pk=document.pk)
    if locked.status != Document.Status.PENDING:
        raise ValidationError("Можно обработать только документ со статусом pending.")

    if status == Document.Status.REJECTED and not rejection_reason.strip():
        raise ValidationError("Для отклонения необходимо указать причину.")

    locked.status = status
    locked.reviewed_by = reviewer
    locked.reviewed_at = timezone.now()
    locked.rejection_reason = (
        rejection_reason.strip() if status == Document.Status.REJECTED else ""
    )
    locked.save(
        update_fields=(
            "status",
            "reviewed_by",
            "reviewed_at",
            "rejection_reason",
            "updated_at",
        )
    )

    # Задача создается только после успешной фиксации транзакции в PostgreSQL.
    transaction.on_commit(
        lambda: notify_user_about_document_status.delay(locked.pk)
    )
    return locked
