from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import (
    UsersListView, UserBlockToggleView, UserSetRoleView,
    SignUpView, ActivationSentView, ActivateAccountView, LogoutView,
    ManagerDashboardView,
)
from .forms import NamespacedPasswordResetForm

app_name = "users"

urlpatterns = [
    # Менеджер: управление пользователями
    path("", UsersListView.as_view(), name="users_list"),
    path("<int:pk>/block-toggle/", UserBlockToggleView.as_view(), name="user_block_toggle"),
    path("<int:pk>/set-role/", UserSetRoleView.as_view(), name="user_set_role"),
    path("dashboard/", ManagerDashboardView.as_view(), name="manager_dashboard"),

    # Аутентификация
    path("signup/", SignUpView.as_view(), name="signup"),
    path("activation-sent/", ActivationSentView.as_view(), name="activation_sent"),
    path("activate/<uuid:token>/", ActivateAccountView.as_view(), name="activate"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),

    # Сброс пароля (всё в НС users)
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name= "registration/password_reset_email_users.html",  # уникальный шаблон
            subject_template_name="registration/password_reset_subject.txt",
            html_email_template_name=None,
            form_class=NamespacedPasswordResetForm,
            success_url=reverse_lazy("users:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url=reverse_lazy("users:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]

