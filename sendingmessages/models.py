from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class UserProfile(models.Model):
    ROLE_USER = "user"
    ROLE_MANAGER = "manager"
    ROLE_CHOICES = [
        (ROLE_USER, "Пользователь"),
        (ROLE_MANAGER, "Менеджер"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=ROLE_USER, verbose_name="Роль")
    is_blocked = models.BooleanField(default=False, verbose_name="Заблокирован")

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

#
class EmailConfirmation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_confirmations")
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Подтверждение email"
        verbose_name_plural = "Подтверждения email"

    def __str__(self):
        return f"{self.user.username} / {self.token} / used={self.is_used}"



class Recipient(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recipients", verbose_name="Владелец")
    email = models.EmailField(unique=True, verbose_name="Email")
    full_name = models.CharField(max_length=255, verbose_name="Ф. И. О.")
    comment = models.TextField(blank=True, verbose_name="Комментарий")

    class Meta:
        verbose_name = "Получатель рассылки"
        verbose_name_plural = "Получатели рассылки"
        ordering = ["full_name", "email"]

    def __str__(self) -> str:
        return f"{self.full_name} <{self.email}>"



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
