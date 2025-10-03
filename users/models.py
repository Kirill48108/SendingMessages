from django.db import models
from django.contrib.auth.models import User
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
        db_table = "sendingmessages_userprofile"  # сохраняем прежнее имя таблицы для безопасного переноса

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

class EmailConfirmation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_confirmations")
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Подтверждение email"
        verbose_name_plural = "Подтверждения email"
        db_table = "sendingmessages_emailconfirmation"  # сохраняем прежнее имя таблицы

    def __str__(self):
        return f"{self.user.username} / {self.token} / used={self.is_used}"
