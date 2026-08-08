"""REST API загрузки, просмотра, удаления и скачивания документов."""

from pathlib import Path

from django.db import transaction
from django.http import FileResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, parsers, permissions, viewsets
from rest_framework.decorators import action

from documents.models import Document
from documents.permissions import CanDeletePendingDocument
from documents.serializers import DocumentCreateSerializer, DocumentSerializer
from documents.tasks import notify_admin_about_new_document


@extend_schema_view(
    list=extend_schema(tags=["Documents"]),
    create=extend_schema(
        tags=["Documents"],
        request={
            "multipart/form-data": DocumentCreateSerializer,
        },
    ),
    retrieve=extend_schema(tags=["Documents"]),
    destroy=extend_schema(tags=["Documents"]),
    download=extend_schema(
        tags=["Documents"],
        responses={(200, "application/octet-stream"): OpenApiTypes.BINARY},
    ),
)
class DocumentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Управление документами с учетом владельца и прав администратора."""

    parser_classes = (parsers.MultiPartParser, parsers.FormParser)
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """Ограничить обычного пользователя его собственными документами."""
        queryset = Document.objects.select_related("owner", "reviewed_by")
        if self.request.user.is_staff:
            return queryset.order_by("-created_at")
        return queryset.filter(owner=self.request.user).order_by("-created_at")

    def get_serializer_class(self):
        """Использовать отдельный сериализатор для безопасной загрузки файла."""
        if self.action == "create":
            return DocumentCreateSerializer
        return DocumentSerializer

    def get_permissions(self):
        """Добавить объектную проверку при удалении документа."""
        if self.action == "destroy":
            return [permissions.IsAuthenticated(), CanDeletePendingDocument()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Назначить владельца и уведомить администратора после коммита."""
        document = serializer.save(owner=self.request.user)
        transaction.on_commit(
            lambda: notify_admin_about_new_document.delay(document.pk)
        )

    def perform_destroy(self, instance: Document) -> None:
        """Удалить запись и связанный файл после успешной транзакции."""
        stored_file = instance.file
        super().perform_destroy(instance)
        transaction.on_commit(lambda: stored_file.delete(save=False))

    @action(detail=True, methods=("get",), url_path="download")
    def download(self, request, *args, **kwargs):
        """Вернуть файл после проверки доступа через queryset представления."""
        document = self.get_object()
        filename = Path(document.file.name).name
        return FileResponse(
            document.file.open("rb"),
            as_attachment=True,
            filename=filename,
        )
