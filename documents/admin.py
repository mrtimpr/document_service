"""Интерфейс административной модерации загруженных документов."""

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import format_html

from documents.models import Document
from documents.services import moderate_document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Предоставить поиск, фильтры и массовые действия модерации."""

    list_display = (
        "id",
        "title",
        "owner",
        "status",
        "created_at",
        "reviewed_at",
    )
    list_filter = ("status", "created_at", "reviewed_at")
    search_fields = ("title", "owner__username", "owner__email")
    exclude = ("file",)
    readonly_fields = (
        "owner",
        "status",
        "secure_file_link",
        "reviewed_by",
        "reviewed_at",
        "created_at",
        "updated_at",
    )
    actions = ("approve_documents", "reject_documents")
    date_hierarchy = "created_at"

    def has_add_permission(self, request) -> bool:
        """Запретить загрузку документов через административную форму."""
        return False

    @admin.display(description="Файл")
    def secure_file_link(self, obj: Document):
        """Показать ссылку на скачивание с проверкой административной сессии."""
        if not obj.pk:
            return "—"
        url = reverse("document-download", args=[obj.pk])
        return format_html('<a href="{}">Скачать документ</a>', url)

    @admin.action(description="Подтвердить выбранные документы")
    def approve_documents(self, request, queryset):
        """Подтвердить выбранные документы со статусом pending."""
        processed = 0
        for document in queryset.filter(status=Document.Status.PENDING):
            try:
                moderate_document(
                    document=document,
                    status=Document.Status.APPROVED,
                    reviewer=request.user,
                )
                processed += 1
            except ValidationError:
                continue
        self.message_user(
            request,
            f"Подтверждено документов: {processed}.",
            level=messages.SUCCESS,
        )

    @admin.action(description="Отклонить выбранные документы")
    def reject_documents(self, request, queryset):
        """Отклонить выбранные документы и зафиксировать причину."""
        processed = 0
        for document in queryset.filter(status=Document.Status.PENDING):
            # Для массового действия используется безопасная причина по умолчанию.
            reason = document.rejection_reason.strip() or "Отклонено администратором."
            try:
                moderate_document(
                    document=document,
                    status=Document.Status.REJECTED,
                    reviewer=request.user,
                    rejection_reason=reason,
                )
                processed += 1
            except ValidationError:
                continue
        self.message_user(
            request,
            f"Отклонено документов: {processed}.",
            level=messages.WARNING,
        )
