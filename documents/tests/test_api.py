"""Тесты REST API загрузки, доступа и скачивания документов."""

from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status

from documents.models import Document

pytestmark = pytest.mark.django_db


def upload_file(name="document.pdf", content_type="application/pdf"):
    return SimpleUploadedFile(name, b"file-content", content_type=content_type)


def test_anonymous_user_cannot_upload(api_client):
    response = api_client.post(
        reverse("document-list"),
        {"title": "Документ", "file": upload_file()},
        format="multipart",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_authenticated_user_uploads_document_and_enqueues_email(
    authenticated_client,
    user,
    django_capture_on_commit_callbacks,
):
    with patch("documents.views.notify_admin_about_new_document.delay") as delay:
        with django_capture_on_commit_callbacks(execute=True):
            response = authenticated_client.post(
                reverse("document-list"),
                {"title": "Договор", "file": upload_file()},
                format="multipart",
            )

    assert response.status_code == status.HTTP_201_CREATED
    document = Document.objects.get()
    assert document.owner == user
    assert document.status == Document.Status.PENDING
    delay.assert_called_once_with(document.pk)


def test_user_cannot_set_status_during_upload(authenticated_client):
    response = authenticated_client.post(
        reverse("document-list"),
        {
            "title": "Договор",
            "file": upload_file(),
            "status": Document.Status.APPROVED,
        },
        format="multipart",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert Document.objects.get().status == Document.Status.PENDING


def test_invalid_mime_type_is_rejected(authenticated_client):
    response = authenticated_client.post(
        reverse("document-list"),
        {"title": "Архив", "file": upload_file("archive.pdf", "application/zip")},
        format="multipart",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "file" in response.data


def test_invalid_extension_is_rejected(authenticated_client):
    response = authenticated_client.post(
        reverse("document-list"),
        {"title": "Архив", "file": upload_file("archive.exe")},
        format="multipart",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "file" in response.data


@override_settings(MAX_DOCUMENT_SIZE_MB=1)
def test_oversized_file_is_rejected(authenticated_client):
    oversized_file = SimpleUploadedFile(
        "large.pdf",
        b"x" * (1024 * 1024 + 1),
        content_type="application/pdf",
    )

    response = authenticated_client.post(
        reverse("document-list"),
        {"title": "Слишком большой файл", "file": oversized_file},
        format="multipart",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "file" in response.data


def test_user_sees_only_own_documents(authenticated_client, user, second_user):
    own = Document.objects.create(
        owner=user,
        title="Свой",
        file=upload_file("own.pdf"),
    )
    Document.objects.create(
        owner=second_user,
        title="Чужой",
        file=upload_file("other.pdf"),
    )

    response = authenticated_client.get(reverse("document-list"))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == own.pk


def test_user_cannot_retrieve_another_users_document(
    authenticated_client,
    second_user,
):
    document = Document.objects.create(
        owner=second_user,
        title="Чужой",
        file=upload_file(),
    )

    response = authenticated_client.get(reverse("document-detail", args=[document.pk]))

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_pending_document_can_be_deleted(authenticated_client, user):
    document = Document.objects.create(
        owner=user,
        title="Черновик",
        file=upload_file(),
    )

    response = authenticated_client.delete(
        reverse("document-detail", args=[document.pk])
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Document.objects.filter(pk=document.pk).exists()


def test_approved_document_cannot_be_deleted(authenticated_client, user):
    document = Document.objects.create(
        owner=user,
        title="Подтвержденный",
        file=upload_file(),
        status=Document.Status.APPROVED,
    )

    response = authenticated_client.delete(
        reverse("document-detail", args=[document.pk])
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Document.objects.filter(pk=document.pk).exists()


def test_owner_can_download_document(authenticated_client, user):
    document = Document.objects.create(
        owner=user,
        title="Скачивание",
        file=upload_file("download.pdf"),
    )

    response = authenticated_client.get(
        reverse("document-download", args=[document.pk])
    )

    assert response.status_code == status.HTTP_200_OK
    assert response["Content-Disposition"].startswith("attachment;")


def test_other_user_cannot_download_document(authenticated_client, second_user):
    document = Document.objects.create(
        owner=second_user,
        title="Чужой файл",
        file=upload_file("private.pdf"),
    )

    response = authenticated_client.get(
        reverse("document-download", args=[document.pk])
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_staff_user_can_download_any_document(api_client, admin_user, user):
    document = Document.objects.create(
        owner=user,
        title="Документ для администратора",
        file=upload_file("admin.pdf"),
    )
    api_client.force_authenticate(user=admin_user)

    response = api_client.get(
        reverse("document-download", args=[document.pk])
    )

    assert response.status_code == status.HTTP_200_OK
