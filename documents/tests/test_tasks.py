"""Тесты фоновых задач отправки email-уведомлений."""

import pytest
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from documents.models import Document
from documents.tasks import (
    notify_admin_about_new_document,
    notify_user_about_document_status,
)

pytestmark = pytest.mark.django_db


def create_document(user, **kwargs):
    values = {
        "owner": user,
        "title": "Заявление",
        "file": SimpleUploadedFile(
            "statement.pdf",
            b"pdf",
            content_type="application/pdf",
        ),
    }
    values.update(kwargs)
    return Document.objects.create(**values)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    ADMIN_EMAIL="moderator@example.com",
    ADMINS=[],
)
def test_admin_notification_email(user):
    document = create_document(user)

    notify_admin_about_new_document(document.pk)

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["moderator@example.com"]
    assert "Загружен новый документ" in mail.outbox[0].subject
    assert user.email in mail.outbox[0].body


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_user_approval_email(user):
    document = create_document(user, status=Document.Status.APPROVED)

    notify_user_about_document_status(document.pk)

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [user.email]
    assert "Подтвержден" in mail.outbox[0].body


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_user_rejection_email_contains_reason(user):
    document = create_document(
        user,
        status=Document.Status.REJECTED,
        rejection_reason="Неверный формат",
    )

    notify_user_about_document_status(document.pk)

    assert len(mail.outbox) == 1
    assert "Неверный формат" in mail.outbox[0].body


def test_tasks_ignore_missing_document():
    assert notify_admin_about_new_document(9999) is None
    assert notify_user_about_document_status(9999) is None
