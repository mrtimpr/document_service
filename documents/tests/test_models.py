"""Тесты модели документа и ее стандартного поведения."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from documents.models import Document

pytestmark = pytest.mark.django_db


def test_document_defaults_to_pending(user):
    document = Document.objects.create(
        owner=user,
        title="Паспорт",
        file=SimpleUploadedFile("passport.pdf", b"pdf", content_type="application/pdf"),
    )

    assert document.status == Document.Status.PENDING
    assert str(document) == "Паспорт — Ожидает проверки"
    assert document.reviewed_at is None


def test_documents_are_ordered_newest_first(user):
    first = Document.objects.create(
        owner=user,
        title="Первый",
        file=SimpleUploadedFile("first.pdf", b"1", content_type="application/pdf"),
    )
    second = Document.objects.create(
        owner=user,
        title="Второй",
        file=SimpleUploadedFile("second.pdf", b"2", content_type="application/pdf"),
    )

    assert list(Document.objects.all()) == [second, first]
