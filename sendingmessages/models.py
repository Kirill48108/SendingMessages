from django.contrib.auth.models import User
from django.utils import timezone


from django.conf import settings
from django.db import models

class Recipient(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipients",
        verbose_name="Владелец",
    )
    email = models.EmailField("Email")  # убрано unique=True
    full_name = models.CharField("Имя", max_length=255, blank=True)
    comment = models.TextField("Комментарий", blank=True)

    class Meta:
        verbose_name = "Получатель"
        verbose_name_plural = "Получатели"
        unique_together = (("owner", "email"),)


    def __str__(self) -> str:
        # В формах и списках будет отображаться email
        return self.email


class Message(models.Model):
    # Прочие поля вашей модели Message
    subject = models.CharField(max_length=255, verbose_name="Тема")
    body = models.TextField(verbose_name="Текст")
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="messages",
        related_query_name="message",
        verbose_name="Владелец",
    )

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"

    def __str__(self) -> str:
        return self.subject


class Mailing(models.Model):
    STATUS_CREATED = "Создана"
    STATUS_RUNNING = "Запущена"
    STATUS_FINISHED = "Завершена"
    STATUS_CHOICES = [
        (STATUS_CREATED, "Создана"),
        (STATUS_RUNNING, "Запущена"),
        (STATUS_FINISHED, "Завершена"),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="mailings",
        related_query_name="mailing",
        verbose_name="Владелец",
    )
    start_at = models.DateTimeField(verbose_name="Дата и время первой отправки")
    end_at = models.DateTimeField(verbose_name="Дата и время окончания отправки")
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_CREATED, verbose_name="Статус"
    )
    is_disabled = models.BooleanField(default=False, verbose_name="Отключена")
    message = models.ForeignKey(
        "Message", on_delete=models.CASCADE, related_name="mailings", verbose_name="Сообщение"
    )
    recipients = models.ManyToManyField(
        "Recipient", related_name="mailings", blank=True, verbose_name="Получатели"
    )

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ["-start_at"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_at__gte=models.F("start_at")), name="mailing_end_after_start"
            )
        ]

    def __str__(self) -> str:
        return f"{self.message.subject} — {self.status}"

    @property
    def is_time_window_active(self) -> bool:
        now = timezone.now()
        return self.start_at <= now <= self.end_at



class MailingAttempt(models.Model):
    STATUS_SUCCESS = "Успешно"
    STATUS_FAILED = "Не успешно"
    STATUS_CHOICES = [
        (STATUS_SUCCESS, "Успешно"),
        (STATUS_FAILED, "Не успешно"),
    ]

    attempted_at = models.DateTimeField(verbose_name="Дата и время попытки")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, verbose_name="Статус")
    server_response = models.TextField(blank=True, verbose_name="Ответ почтового сервера")
    mailing = models.ForeignKey(
        Mailing, on_delete=models.CASCADE, related_name="attempts", verbose_name="Рассылка"
    )

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылки"
        ordering = ["-attempted_at"]

    def __str__(self) -> str:
        return f"{self.mailing} — {self.status} @ {self.attempted_at:%Y-%m-%d %H:%M:%S}"
