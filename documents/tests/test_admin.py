"""Тесты массовых действий модерации в Django Admin."""

from unittest.mock import patch

import pytest
from django.contrib.admin.sites import AdminSite
from django.core.files.uploadedfile import SimpleUploadedFile

from documents.admin import DocumentAdmin
from documents.models import Document

pytestmark = pytest.mark.django_db


def create_document(user, **kwargs):
    values = {
        "owner": user,
        "title": "Документ",
        "file": SimpleUploadedFile(
            "document.pdf",
            b"pdf",
            content_type="application/pdf",
        ),
    }
    values.update(kwargs)
    return Document.objects.create(**values)


def test_admin_approve_action(admin_user, user, rf, django_capture_on_commit_callbacks):
    document = create_document(user)
    request = rf.post("/admin/documents/document/")
    request.user = admin_user
    model_admin = DocumentAdmin(Document, AdminSite())

    with patch.object(model_admin, "message_user"):
        with patch("documents.services.notify_user_about_document_status.delay"):
            with django_capture_on_commit_callbacks(execute=True):
                model_admin.approve_documents(
                    request,
                    Document.objects.filter(pk=document.pk),
                )

    document.refresh_from_db()
    assert document.status == Document.Status.APPROVED
    assert document.reviewed_by == admin_user


def test_admin_reject_action_uses_default_reason(
    admin_user,
    user,
    rf,
    django_capture_on_commit_callbacks,
):
    document = create_document(user)
    request = rf.post("/admin/documents/document/")
    request.user = admin_user
    model_admin = DocumentAdmin(Document, AdminSite())

    with patch.object(model_admin, "message_user"):
        with patch("documents.services.notify_user_about_document_status.delay"):
            with django_capture_on_commit_callbacks(execute=True):
                model_admin.reject_documents(
                    request,
                    Document.objects.filter(pk=document.pk),
                )

    document.refresh_from_db()
    assert document.status == Document.Status.REJECTED
    assert document.rejection_reason == "Отклонено администратором."


def test_admin_disables_manual_document_creation(admin_user, rf):
    request = rf.get("/admin/documents/document/add/")
    request.user = admin_user
    model_admin = DocumentAdmin(Document, AdminSite())

    assert model_admin.has_add_permission(request) is False


def test_admin_secure_file_link_contains_download_url(user):
    document = create_document(user)
    model_admin = DocumentAdmin(Document, AdminSite())

    link = str(model_admin.secure_file_link(document))

    assert f"/api/documents/{document.pk}/download/" in link
