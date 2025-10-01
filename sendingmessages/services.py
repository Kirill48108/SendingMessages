from typing import Dict
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
import logging

from .models import Mailing, MailingAttempt, EmailConfirmation

logger = logging.getLogger(__name__)

def _get_from_email() -> str:
    return getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")

def send_activation_email(request, user: User) -> None:
    confirm = EmailConfirmation.objects.create(user=user)
    activate_url = request.build_absolute_uri(reverse("activate", args=[str(confirm.token)]))
    subject = "Подтверждение регистрации"
    body = f"Здравствуйте, {user.username}!\nЧтобы активировать аккаунт, перейдите по ссылке: {activate_url}"
    send_mail(subject=subject, message=body, from_email=_get_from_email(), recipient_list=[user.email])
    logger.info("Activation email queued to %s (user_id=%s, token=%s)", user.email, user.id, confirm.token)

def send_mailing(mailing: Mailing) -> Dict[str, int]:
    """
    Отправка писем по рассылке, запись MailingAttempt на каждого получателя.
    Учитывает отключение рассылки и блокировку владельца.
    """
    owner_profile = getattr(mailing.owner, "profile", None)
    if mailing.is_disabled:
        logger.warning("Skip mailing id=%s: mailing disabled", mailing.id)
        return {"total": 0, "success": 0, "failed": 0}
    if owner_profile and owner_profile.is_blocked:
        logger.warning("Skip mailing id=%s: owner is blocked (user_id=%s)", mailing.id, mailing.owner_id)
        return {"total": 0, "success": 0, "failed": 0}

    recipients = list(mailing.recipients.all())
    total = success = failed = 0
    logger.info("Start sending mailing id=%s to %s recipients (status=%s)", mailing.id, len(recipients), mailing.status)

    if mailing.status == Mailing.STATUS_CREATED:
        mailing.status = Mailing.STATUS_RUNNING
        mailing.save(update_fields=["status"])
        logger.info("Mailing id=%s status changed to RUNNING", mailing.id)

    for r in recipients:
        total += 1
        try:
            sent = send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=_get_from_email(),
                recipient_list=[r.email],
                fail_silently=False,
            )
            if sent > 0:
                MailingAttempt.objects.create(
                    mailing=mailing,
                    attempted_at=timezone.now(),
                    status=MailingAttempt.STATUS_SUCCESS,
                    server_response="",
                )
                success += 1
                logger.debug("Mail sent to %s for mailing id=%s", r.email, mailing.id)
            else:
                MailingAttempt.objects.create(
                    mailing=mailing,
                    attempted_at=timezone.now(),
                    status=MailingAttempt.STATUS_FAILED,
                    server_response="Нет подтверждения об отправке",
                )
                failed += 1
                logger.error("Mail not confirmed sent to %s for mailing id=%s", r.email, mailing.id)
        except Exception as exc:
            MailingAttempt.objects.create(
                mailing=mailing,
                attempted_at=timezone.now(),
                status=MailingAttempt.STATUS_FAILED,
                server_response=str(exc),
            )
            failed += 1
            logger.exception("Mail send error to %s for mailing id=%s: %s", r.email, mailing.id, exc)

    if timezone.now() >= mailing.end_at and mailing.status != Mailing.STATUS_FINISHED:
        mailing.status = Mailing.STATUS_FINISHED
        mailing.save(update_fields=["status"])
        logger.info("Mailing id=%s status changed to FINISHED (time window ended)", mailing.id)

    logger.info("Finish mailing id=%s: total=%s success=%s failed=%s", mailing.id, total, success, failed)
    return {"total": total, "success": success, "failed": failed}

def process_due_mailings() -> int:
    """
    Шедулируемая задача: отправляет все рассылки, которые активны по времени,
    не отключены, и находятся в статусе Создана/Запущена.
    Возвращает количество обработанных рассылок.
    """
    now = timezone.now()
    qs = Mailing.objects.filter(
        start_at__lte=now,
        end_at__gte=now,
        is_disabled=False,
        status__in=[Mailing.STATUS_CREATED, Mailing.STATUS_RUNNING],
    ).select_related("message", "owner").prefetch_related("recipients")

    processed = 0
    for mailing in qs:
        logger.info("Scheduled processing of mailing id=%s", mailing.id)
        send_mailing(mailing)
        processed += 1
    logger.info("Scheduled job finished. Processed messages: %s", processed)
    return processed
