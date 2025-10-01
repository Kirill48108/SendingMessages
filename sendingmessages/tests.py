from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch
from django.utils import timezone
import uuid

from .models import (
    UserProfile, Recipient, Message, Mailing, MailingAttempt, EmailConfirmation
)

# Общие настройки для почты в тестах (локальная "память")
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class BaseSetupMixin(TestCase):
    def setUp(self):
        # Обычный пользователь (владелец данных)
        self.user = User.objects.create_user(
            username="u1", password="p", is_active=True, email="u1@example.com"
        )
        UserProfile.objects.create(user=self.user, role=UserProfile.ROLE_USER, is_blocked=False)

        # Второй обычный пользователь (чтобы проверить запрет редактирования чужих)
        self.user2 = User.objects.create_user(
            username="u2", password="p", is_active=True, email="u2@example.com"
        )
        UserProfile.objects.create(user=self.user2, role=UserProfile.ROLE_USER, is_blocked=False)

        # Менеджер
        self.manager = User.objects.create_user(
            username="m1", password="p", is_active=True, email="m1@example.com"
        )
        UserProfile.objects.create(user=self.manager, role=UserProfile.ROLE_MANAGER, is_blocked=False)

        # Данные владельца
        self.rec1 = Recipient.objects.create(owner=self.user, email="r1@example.com", full_name="R One", comment="")
        self.rec2 = Recipient.objects.create(owner=self.user, email="r2@example.com", full_name="R Two", comment="")
        self.msg = Message.objects.create(owner=self.user, subject="Subj", body="Body")

        now = timezone.now()
        self.mailing = Mailing.objects.create(
            owner=self.user,
            start_at=now - timezone.timedelta(minutes=1),
            end_at=now + timezone.timedelta(minutes=2),
            status=Mailing.STATUS_CREATED,
            is_disabled=False,
            message=self.msg,
        )
        self.mailing.recipients.set([self.rec1, self.rec2])

        self.client = Client()


class TemplatesSeparationTests(BaseSetupMixin):
    def test_messages_list_uses_messages_template(self):
        self.client.login(username="u1", password="p")
        resp = self.client.get(reverse("messages_list"))
        self.assertTemplateUsed(resp, "messages/list.html")
        self.assertContains(resp, "Сообщения")

    def test_mailings_list_uses_mailings_template(self):
        self.client.login(username="u1", password="p")
        resp = self.client.get(reverse("mailings_list"))
        self.assertTemplateUsed(resp, "mailings/list.html")
        self.assertContains(resp, "Рассылки")


class MailingSendViewTests(BaseSetupMixin):
    @patch("sendingmessages.views.send_mailing_service")
    def test_user_can_send_own_mailing_and_status_changes(self, mock_send):
        mock_send.return_value = {"total": 2, "success": 2, "failed": 0}
        self.client.login(username="u1", password="p")

        resp = self.client.post(reverse("mailings_send", args=[self.mailing.pk]), follow=True)
        self.assertEqual(resp.status_code, 200)

        self.mailing.refresh_from_db()
        self.assertIn(self.mailing.status, [Mailing.STATUS_RUNNING, Mailing.STATUS_FINISHED])

    @patch("sendingmessages.views.send_mailing_service")
    def test_manager_can_send_someones_mailing(self, mock_send):
        mock_send.return_value = {"total": 1, "success": 1, "failed": 0}
        self.client.login(username="m1", password="p")

        resp = self.client.post(reverse("mailings_send", args=[self.mailing.pk]), follow=True)
        self.assertEqual(resp.status_code, 200)

        self.mailing.refresh_from_db()
        self.assertIn(self.mailing.status, [Mailing.STATUS_RUNNING, Mailing.STATUS_FINISHED])

    def test_user_cannot_send_disabled_mailing(self):
        self.mailing.is_disabled = True
        self.mailing.save(update_fields=["is_disabled"])
        self.client.login(username="u1", password="p")

        resp = self.client.post(reverse("mailings_send", args=[self.mailing.pk]), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.mailing.refresh_from_db()
        # статус не должен становиться RUNNING
        self.assertNotEqual(self.mailing.status, Mailing.STATUS_RUNNING)


class ManagerUsersPageTests(BaseSetupMixin):
    def test_only_manager_can_open_users_page(self):
        # обычный пользователь -> редирект/нет доступа
        self.client.login(username="u1", password="p")
        resp = self.client.get(reverse("users_list"), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.client.logout()

        # менеджер -> OK
        self.client.login(username="m1", password="p")
        resp = self.client.get(reverse("users_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Пользователи сервиса")


# Тесты регистрации и активации
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class RegistrationActivationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_signup_creates_inactive_user_and_confirmation(self):
        from django.core import mail

        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPass#123",
        }
        resp = self.client.post(reverse("signup"), data, follow=True)
        self.assertEqual(resp.status_code, 200)
        # Пользователь создан и не активен
        user = User.objects.get(username="newuser")
        self.assertFalse(user.is_active)
        # Профиль создан
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.role, UserProfile.ROLE_USER)
        # Письмо в outbox
        self.assertGreaterEqual(len(mail.outbox), 1)
        # Существует запись EmailConfirmation
        self.assertTrue(EmailConfirmation.objects.filter(user=user, is_used=False).exists())

    def test_activate_account_by_token(self):
        # Подготовка: неактивный пользователь + токен
        user = User.objects.create_user(username="inactive", password="p", email="inactive@example.com", is_active=False)
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_USER, is_blocked=False)
        token = uuid.uuid4()
        EmailConfirmation.objects.create(user=user, token=token, is_used=False)

        # Переходим по ссылке активации
        resp = self.client.get(reverse("activate", kwargs={"token": token}), follow=True)
        self.assertEqual(resp.status_code, 200)

        user.refresh_from_db()
        self.assertTrue(user.is_active)
        confirm = EmailConfirmation.objects.get(user=user, token=token)
        self.assertTrue(confirm.is_used)


# Запрет редактирования/удаления чужих объектов (для менеджеров и обычных пользователей)
class EditForbiddenTests(BaseSetupMixin):
    def test_manager_cannot_edit_others_recipient(self):
        self.client.login(username="m1", password="p")
        url = reverse("recipients_edit", kwargs={"pk": self.rec1.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_other_user_cannot_edit_others_recipient(self):
        self.client.login(username="u2", password="p")
        url = reverse("recipients_edit", kwargs={"pk": self.rec1.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_manager_cannot_edit_others_message(self):
        self.client.login(username="m1", password="p")
        url = reverse("messages_edit", kwargs={"pk": self.msg.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_other_user_cannot_edit_others_message(self):
        self.client.login(username="u2", password="p")
        url = reverse("messages_edit", kwargs={"pk": self.msg.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_manager_cannot_edit_others_mailing(self):
        self.client.login(username="m1", password="p")
        url = reverse("mailings_edit", kwargs={"pk": self.mailing.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_other_user_cannot_edit_others_mailing(self):
        self.client.login(username="u2", password="p")
        url = reverse("mailings_edit", kwargs={"pk": self.mailing.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)


# Кэш: используем LocMem в тесте, чтобы не требовать поднятого Redis
@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-locmem",
            "TIMEOUT": 60,
        }
    }
)
class CacheBackendTests(TestCase):
    def test_cache_backend_is_working(self):
        from django.core.cache import caches
        cache = caches['default']
        cache.set("k", "v", 10)
        self.assertEqual(cache.get("k"), "v")

