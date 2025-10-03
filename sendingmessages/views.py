from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.http import HttpResponseRedirect, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_cookie
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View, FormView
)

import logging

from .models import Recipient, Message, Mailing, MailingAttempt
from users.models import UserProfile
from .services import send_mailing as send_mailing_service

logger = logging.getLogger(__name__)


# =========================
# МИКСИНЫ доступа / служебные
# =========================

class BlockedCheckMixin(UserPassesTestMixin):
    """
    Запрещает доступ заблокированным пользователям (profile.is_blocked=True).
    При запрете показывает сообщение и уводит на главную.
    """
    def test_func(self):
        profile = getattr(self.request.user, "profile", None)
        return not (profile and profile.is_blocked)

    def handle_no_permission(self):
        messages.error(self.request, "Ваш аккаунт заблокирован. Обратитесь к менеджеру.")
        return HttpResponseRedirect(reverse("home"))

class OwnerCreateMixin:
    """
    Автопривязка request.user в поле owner для создаваемых объектов.
    Не наследуется от LoginRequiredMixin, чтобы избежать конфликтов MRO.
    """
    owner_field_name = "owner"

    def form_valid(self, form):
        model_fields = {f.name for f in form._meta.model._meta.get_fields()}
        if self.owner_field_name in model_fields and not form.instance.pk:
            setattr(form.instance, self.owner_field_name, self.request.user)
        return super().form_valid(form)


class OwnerAssignMixin:
    """
    Автоматически проставляет owner текущего пользователя при создании объекта.
    """
    pass

class OwnerOrManagerQuerysetMixin:
    """
    Менеджер видит всё, обычный пользователь — только свои объекты.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        role = getattr(getattr(user, "profile", None), "role", UserProfile.ROLE_USER)
        if role == UserProfile.ROLE_MANAGER:
            return qs
        return qs.filter(owner=user)

class OwnerOnlyQuerysetMixin:
    """
    Редактировать/удалять можно только свои объекты (даже менеджерам запрещено редактировать чужие).
    """
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        return qs.filter(owner=user)

class ManagerRequiredMixin(UserPassesTestMixin):
    """
    Доступ только для менеджеров.
    """
    def test_func(self):
        user = self.request.user
        role = getattr(getattr(user, "profile", None), "role", UserProfile.ROLE_USER)
        return user.is_authenticated and role == UserProfile.ROLE_MANAGER

    def handle_no_permission(self):
        messages.error(self.request, "Доступ разрешён только менеджерам.")
        return HttpResponseRedirect(reverse("home"))




# =========================
# Главная
# =========================

@method_decorator(vary_on_cookie, name="dispatch")
class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["mailings_total"] = Mailing.objects.count()
        ctx["mailings_active"] = Mailing.objects.filter(status=Mailing.STATUS_RUNNING).count()
        ctx["unique_recipients"] = Recipient.objects.values("email").distinct().count()
        return ctx

# =========================
# Клиенты
# =========================

@method_decorator(vary_on_cookie, name="dispatch")
class RecipientListView(LoginRequiredMixin, BlockedCheckMixin, OwnerOrManagerQuerysetMixin, ListView):
    model = Recipient
    template_name = "recipients/list.html"
    context_object_name = "recipients"

class RecipientDetailView(LoginRequiredMixin, BlockedCheckMixin, OwnerOrManagerQuerysetMixin, DetailView):
    model = Recipient
    template_name = "recipients/detail.html"
    context_object_name = "recipient"

class RecipientCreateView(LoginRequiredMixin, BlockedCheckMixin, OwnerCreateMixin, CreateView):
    model = Recipient
    fields = ["email", "full_name", "comment"]
    template_name = "recipients/form.html"
    success_url = reverse_lazy("recipients_list")


class RecipientUpdateView(LoginRequiredMixin, BlockedCheckMixin, OwnerOnlyQuerysetMixin, UpdateView):
    model = Recipient
    fields = ["email", "full_name", "comment"]
    template_name = "recipients/form.html"
    success_url = reverse_lazy("recipients_list")

class RecipientDeleteView(LoginRequiredMixin, BlockedCheckMixin, OwnerOnlyQuerysetMixin, DeleteView):
    model = Recipient
    template_name = "recipients/confirm_delete.html"
    success_url = reverse_lazy("recipients_list")

# =========================
# Сообщения
# =========================

@method_decorator(vary_on_cookie, name="dispatch")
class MessageListView(LoginRequiredMixin, BlockedCheckMixin, OwnerOrManagerQuerysetMixin, ListView):
    model = Message
    template_name = "messages/list.html"
    context_object_name = "message_list"

class MessageDetailView(LoginRequiredMixin, BlockedCheckMixin, OwnerOrManagerQuerysetMixin, DetailView):
    model = Message
    template_name = "messages/detail.html"
    context_object_name = "message"

class MessageCreateView(LoginRequiredMixin, BlockedCheckMixin, OwnerCreateMixin, CreateView):
    model = Message
    fields = ["subject", "body"]
    template_name = "messages/form.html"
    success_url = reverse_lazy("messages_list")


class MessageUpdateView(LoginRequiredMixin, BlockedCheckMixin, OwnerOnlyQuerysetMixin, UpdateView):
    model = Message
    fields = ["subject", "body"]
    template_name = "messages/form.html"
    success_url = reverse_lazy("messages_list")

class MessageDeleteView(LoginRequiredMixin, BlockedCheckMixin, OwnerOnlyQuerysetMixin, DeleteView):
    model = Message
    template_name = "messages/confirm_delete.html"
    success_url = reverse_lazy("messages_list")

# =========================
# Рассылки
# =========================

@method_decorator(vary_on_cookie, name="dispatch")
class MailingListView(LoginRequiredMixin, BlockedCheckMixin, OwnerOrManagerQuerysetMixin, ListView):
    model = Mailing
    template_name = "mailings/list.html"
    context_object_name = "mailing_list"

class MailingDetailView(LoginRequiredMixin, BlockedCheckMixin, OwnerOrManagerQuerysetMixin, DetailView):
    model = Mailing
    template_name = "mailings/detail.html"
    context_object_name = "mailing"

class MailingCreateView(LoginRequiredMixin, BlockedCheckMixin, OwnerCreateMixin, CreateView):
    model = Mailing
    fields = ["start_at", "end_at", "status", "message", "recipients", "is_disabled"]
    template_name = "mailings/form.html"
    success_url = reverse_lazy("mailings_list")


class MailingUpdateView(LoginRequiredMixin, BlockedCheckMixin, OwnerOnlyQuerysetMixin, UpdateView):
    model = Mailing
    fields = ["start_at", "end_at", "status", "message", "recipients", "is_disabled"]
    template_name = "mailings/form.html"
    success_url = reverse_lazy("mailings_list")

class MailingDeleteView(LoginRequiredMixin, BlockedCheckMixin, OwnerOnlyQuerysetMixin, DeleteView):
    model = Mailing
    template_name = "mailings/confirm_delete.html"
    success_url = reverse_lazy("mailings_list")

class MailingSendView(LoginRequiredMixin, BlockedCheckMixin, OwnerOrManagerQuerysetMixin, View):
    model = Mailing

    def post(self, request, pk: int):
        mailing = get_object_or_404(Mailing, pk=pk)

        is_manager = getattr(getattr(request.user, "profile", None), "role", UserProfile.ROLE_USER) == UserProfile.ROLE_MANAGER
        if not is_manager and mailing.owner != request.user:
            messages.error(request, "Нет прав на запуск этой рассылки.")
            logger.warning("User %s attempted to run mailing %s without permission", request.user.id, mailing.id)
            return HttpResponseRedirect(reverse("mailings_detail", args=[pk]))

        if mailing.is_disabled:
            messages.error(request, "Рассылка отключена менеджером.")
            logger.warning("Attempt to run disabled mailing %s by user %s", mailing.id, request.user.id)
            return HttpResponseRedirect(reverse("mailings_detail", args=[pk]))

        now = timezone.now()
        if mailing.end_at and now > mailing.end_at:
            if mailing.status != Mailing.STATUS_FINISHED:
                mailing.status = Mailing.STATUS_FINISHED
                mailing.save(update_fields=["status"])
            messages.error(request, "Окно времени рассылки истекло.")
            return HttpResponseRedirect(reverse("mailings_detail", args=[pk]))

        if mailing.start_at and now < mailing.start_at:
            messages.error(request, "Время запуска рассылки ещё не наступило.")
            return HttpResponseRedirect(reverse("mailings_detail", args=[pk]))

        logger.info("User %s triggered manual send for mailing %s", request.user.id, mailing.id)
        result = send_mailing_service(mailing)

        new_status = Mailing.STATUS_RUNNING
        if mailing.end_at and timezone.now() > mailing.end_at:
            new_status = Mailing.STATUS_FINISHED
        if mailing.status != new_status:
            mailing.status = new_status
            mailing.save(update_fields=["status"])

        messages.info(
            request,
            f"Отправка завершена: всего={result['total']}, успешно={result['success']}, ошибки={result['failed']}",
        )
        return HttpResponseRedirect(reverse("mailings_detail", args=[pk]))

    def get(self, request, pk: int):
        return HttpResponseNotAllowed(permitted_methods=["POST"])


# =========================
# Статистика
# =========================

class StatsView(LoginRequiredMixin, BlockedCheckMixin, TemplateView):
    template_name = "stats/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        is_manager = getattr(getattr(user, "profile", None), "role", UserProfile.ROLE_USER) == UserProfile.ROLE_MANAGER

        mailings = Mailing.objects.all() if is_manager else Mailing.objects.filter(owner=user)
        attempts = MailingAttempt.objects.filter(mailing__in=mailings)

        agg = attempts.values("status").annotate(cnt=Count("id"))
        success = next((a["cnt"] for a in agg if a["status"] == MailingAttempt.STATUS_SUCCESS), 0)
        failed = next((a["cnt"] for a in agg if a["status"] == MailingAttempt.STATUS_FAILED), 0)

        ctx.update({
            "mailings_count": mailings.count(),
            "attempts_success": success,
            "attempts_failed": failed,
            "attempts_total": success + failed,
            "messages_sent": success,  # количество отправленных сообщений (успешные попытки)
        })
        return ctx






