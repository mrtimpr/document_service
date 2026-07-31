"""Фоновые Celery-задачи отправки уведомлений по электронной почте."""

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from documents.models import Document


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def notify_admin_about_new_document(_task, document_id: int) -> None:
    """Уведомить администратора о новом загруженном документе."""
    try:
        document = Document.objects.select_related("owner").get(pk=document_id)
    except Document.DoesNotExist:
        return

    # Множество исключает повторную отправку на один и тот же адрес.
    recipients = {email for _, email in settings.ADMINS if email}
    if settings.ADMIN_EMAIL:
        recipients.add(settings.ADMIN_EMAIL)
    if not recipients:
        return

    send_mail(
        subject="Загружен новый документ",
        message=(
            f"Пользователь {document.owner.email} загрузил документ "
            f'«{document.title}». ID документа: {document.pk}.'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=sorted(recipients),
        fail_silently=False,
    )


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def notify_user_about_document_status(_task, document_id: int) -> None:
    """Уведомить владельца о подтверждении или отклонении документа."""
    try:
        document = Document.objects.select_related("owner").get(pk=document_id)
    except Document.DoesNotExist:
        return

    if not document.owner.email:
        return

    message = (
        f'Документ «{document.title}» получил статус: '
        f"{document.get_status_display()}."
    )
    if document.status == Document.Status.REJECTED:
        reason = document.rejection_reason or "Причина не указана."
        message = f"{message}\nПричина отклонения: {reason}"

    send_mail(
        subject="Результат проверки документа",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[document.owner.email],
        fail_silently=False,
    )
