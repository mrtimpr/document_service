import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import documents.validators


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Document",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=255, verbose_name="Название")),
                (
                    "file",
                    models.FileField(
                        upload_to="documents/%Y/%m/%d/",
                        validators=[
                            django.core.validators.FileExtensionValidator(
                                ["pdf", "doc", "docx", "jpg", "jpeg", "png", "txt"]
                            ),
                            documents.validators.validate_file_size,
                        ],
                        verbose_name="Файл",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Ожидает проверки"),
                            ("approved", "Подтвержден"),
                            ("rejected", "Отклонен"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                        verbose_name="Статус",
                    ),
                ),
                ("rejection_reason", models.TextField(blank=True, verbose_name="Причина отклонения")),
                ("reviewed_at", models.DateTimeField(blank=True, null=True, verbose_name="Дата проверки")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Дата изменения")),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="documents",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Владелец",
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reviewed_documents",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Проверил",
                    ),
                ),
            ],
            options={
                "verbose_name": "Документ",
                "verbose_name_plural": "Документы",
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddIndex(
            model_name="document",
            index=models.Index(fields=["owner", "status"], name="doc_owner_status_idx"),
        ),
    ]
