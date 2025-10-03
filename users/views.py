from django.contrib import messages
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponseNotAllowed, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView, View, FormView

from .models import UserProfile
from sendingmessages.views import BlockedCheckMixin, ManagerRequiredMixin
from sendingmessages.services import send_activation_email
from django.contrib.auth.views import LogoutView as DjangoLogoutView

class LogoutView(DjangoLogoutView):
    """
    GET: показать страницу подтверждения с POST-формой.
    POST: выполнить выход.
    """
    http_method_names = ["get", "post", "options"]
    template_name = "registration/logout.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)



# Регистрация и активация
class SignUpView(FormView):
    template_name = "auth/signup.html"
    success_url = reverse_lazy("activation_sent")


# Менеджер: список пользователей
class UsersListView(LoginRequiredMixin, BlockedCheckMixin, ManagerRequiredMixin, TemplateView):
    template_name = "users/list.html"


    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        users = User.objects.select_related("profile").order_by("username")
        ctx["users"] = users
        ctx["ROLE_USER"] = UserProfile.ROLE_USER
        ctx["ROLE_MANAGER"] = UserProfile.ROLE_MANAGER
        return ctx

class UserBlockToggleView(LoginRequiredMixin, BlockedCheckMixin, ManagerRequiredMixin, View):
    def post(self, request, pk: int):
        target = get_object_or_404(User, pk=pk)
        profile = getattr(target, "profile", None) or UserProfile.objects.create(
            user=target, role=UserProfile.ROLE_USER, is_blocked=False
        )
        profile.is_blocked = not profile.is_blocked
        profile.save(update_fields=["is_blocked"])
        state = "заблокирован" if profile.is_blocked else "разблокирован"
        messages.success(request, f"Пользователь {target.username} {state}.")
        return HttpResponseRedirect(reverse("users_list"))

    def get(self, request, pk: int):
        return HttpResponseNotAllowed(permitted_methods=["POST"])

class UserSetRoleView(LoginRequiredMixin, BlockedCheckMixin, ManagerRequiredMixin, View):
    def post(self, request, pk: int):
        target = get_object_or_404(User, pk=pk)
        new_role = request.POST.get("role")
        if new_role not in (UserProfile.ROLE_USER, UserProfile.ROLE_MANAGER):
            messages.error(request, "Некорректная роль.")
            return HttpResponseRedirect(reverse("users_list"))

        profile = getattr(target, "profile", None) or UserProfile.objects.create(
            user=target, role=UserProfile.ROLE_USER, is_blocked=False
        )
        profile.role = new_role
        profile.save(update_fields=["role"])
        role_human = "Менеджер" if new_role == UserProfile.ROLE_MANAGER else "Пользователь"
        messages.success(request, f"Роль пользователя {target.username} изменена на «{role_human}».")
        return HttpResponseRedirect(reverse("users_list"))

    def get(self, request, pk: int):
        return HttpResponseNotAllowed(permitted_methods=["POST"])

# Регистрация и активация
class SignUpView(FormView):
    template_name = "auth/signup.html"
    success_url = reverse_lazy("activation_sent")

    def get_form(self, form_class=None):
        from django import forms
        class _Form(forms.Form):
            username = forms.CharField(max_length=150, label="Логин")
            email = forms.EmailField(label="Email")
            password = forms.CharField(widget=forms.PasswordInput, label="Пароль")
        return _Form(self.request.POST or None)

    def form_valid(self, form):
        from django.db import IntegrityError, transaction
        username = form.cleaned_data["username"].strip()
        email = form.cleaned_data["email"].strip()
        password = form.cleaned_data["password"]

        if User.objects.filter(Q(username__iexact=username) | Q(email__iexact=email)).exists():
            form.add_error(None, "Пользователь с таким логином или email уже существует")
            return self.form_invalid(form)

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_active=False,
                )
        except IntegrityError:
            form.add_error(None, "Пользователь с таким логином или email уже существует")
            return self.form_invalid(form)

        UserProfile.objects.get_or_create(user=user, defaults={"role": UserProfile.ROLE_USER})
        send_activation_email(self.request, user)
        return super().form_valid(form)

class ActivationSentView(TemplateView):
    template_name = "auth/activation_sent.html"

class ActivateAccountView(View):
    def get(self, request, token):
        confirm = get_object_or_404(EmailConfirmation, token=token, is_used=False)
        user = confirm.user
        user.is_active = True
        user.save(update_fields=["is_active"])
        confirm.is_used = True
        confirm.save(update_fields=["is_used"])
        messages.success(request, "Аккаунт активирован. Выполните вход.")
        return HttpResponseRedirect(reverse("login"))

