from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    UsersListView, UserBlockToggleView, UserSetRoleView,
    SignUpView, ActivationSentView, ActivateAccountView, LogoutView
)


urlpatterns = [
    # Менеджер: управление пользователями
    path("users/", UsersListView.as_view(), name="users_list"),
    path("users/<int:pk>/block-toggle/", UserBlockToggleView.as_view(), name="user_block_toggle"),
    path("users/<int:pk>/set-role/", UserSetRoleView.as_view(), name="user_set_role"),

    # Аутентификация
    path("signup/", SignUpView.as_view(), name="signup"),
    path("activation-sent/", ActivationSentView.as_view(), name="activation_sent"),
    path("activate/<uuid:token>/", ActivateAccountView.as_view(), name="activate"),

    # login/logout
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),


    # сброс пароля
    path("password-reset/", auth_views.PasswordResetView.as_view(template_name="registration/password_reset_form.html"), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"), name="password_reset_complete"),
]
