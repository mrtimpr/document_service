"""Тесты атомарного сервисного слоя модерации документов."""

from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from documents.models import Document
from documents.services import moderate_document

pytestmark = pytest.mark.django_db


def create_document(user, status=Document.Status.PENDING):
    return Document.objects.create(
        owner=user,
        title="Документ",
        file=SimpleUploadedFile("document.pdf", b"pdf", content_type="application/pdf"),
        status=status,
    )


def test_approve_document(admin_user, user, django_capture_on_commit_callbacks):
    document = create_document(user)

    with patch("documents.services.notify_user_about_document_status.delay") as delay:
        with django_capture_on_commit_callbacks(execute=True):
            result = moderate_document(
                document=document,
                status=Document.Status.APPROVED,
                reviewer=admin_user,
            )

    assert result.status == Document.Status.APPROVED
    assert result.reviewed_by == admin_user
    assert result.reviewed_at is not None
    assert result.rejection_reason == ""
    delay.assert_called_once_with(document.pk)


def test_rejection_requires_reason(admin_user, user):
    document = create_document(user)

    with pytest.raises(ValidationError, match="необходимо указать причину"):
        moderate_document(
            document=document,
            status=Document.Status.REJECTED,
            reviewer=admin_user,
        )


def test_reject_document(admin_user, user, django_capture_on_commit_callbacks):
    document = create_document(user)

    with patch("documents.services.notify_user_about_document_status.delay"):
        with django_capture_on_commit_callbacks(execute=True):
            result = moderate_document(
                document=document,
                status=Document.Status.REJECTED,
                reviewer=admin_user,
                rejection_reason="Нечитаемый файл",
            )

    assert result.status == Document.Status.REJECTED
    assert result.rejection_reason == "Нечитаемый файл"


def test_already_processed_document_cannot_be_processed_again(admin_user, user):
    document = create_document(user, status=Document.Status.APPROVED)

    with pytest.raises(ValidationError, match="только документ"):
        moderate_document(
            document=document,
            status=Document.Status.APPROVED,
            reviewer=admin_user,
        )


def test_invalid_status_is_rejected(admin_user, user):
    document = create_document(user)

    with pytest.raises(ValidationError, match="Недопустимый"):
        moderate_document(document=document, status="unknown", reviewer=admin_user)
