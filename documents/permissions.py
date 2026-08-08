"""Объектные разрешения для операций с документами."""

from rest_framework.permissions import BasePermission

from documents.models import Document


class CanDeletePendingDocument(BasePermission):
    """Разрешить владельцу удалять только документ, ожидающий проверки."""

    message = "Удалять можно только собственные документы, ожидающие проверки."

    def has_object_permission(self, request, view, obj: Document) -> bool:
        """Проверить владельца документа и его текущий статус."""
        return obj.owner_id == request.user.id and obj.status == Document.Status.PENDING
