from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    HomeView, StatsView,
    SignUpView, ActivationSentView, ActivateAccountView,
    RecipientListView, RecipientDetailView, RecipientCreateView, RecipientUpdateView, RecipientDeleteView,
    MessageListView, MessageDetailView, MessageCreateView, MessageUpdateView, MessageDeleteView,
    MailingListView, MailingDetailView, MailingCreateView, MailingUpdateView, MailingDeleteView, MailingSendView,
    UsersListView,UserBlockToggleView,UserSetRoleView
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("stats/", StatsView.as_view(), name="stats"),


    # Менеджер: управление пользователями
    path("users/", UsersListView.as_view(), name="users_list"),
    path("users/<int:pk>/block-toggle/", UserBlockToggleView.as_view(), name="user_block_toggle"),
    path("users/<int:pk>/set-role/", UserSetRoleView.as_view(), name="user_set_role"),


    # Аутентификация
    path("signup/", SignUpView.as_view(), name="signup"),
    path("activation-sent/", ActivationSentView.as_view(), name="activation_sent"),
    path("activate/<uuid:token>/", ActivateAccountView.as_view(), name="activate"),

    path("login/", auth_views.LoginView.as_view(template_name="auth/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),

    path("password-reset/", auth_views.PasswordResetView.as_view(template_name="auth/password_reset_form.html"), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="auth/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="auth/password_reset_confirm.html"), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name="auth/password_reset_complete.html"), name="password_reset_complete"),

    # Клиенты
    path("recipients/", RecipientListView.as_view(), name="recipients_list"),
    path("recipients/new/", RecipientCreateView.as_view(), name="recipients_create"),
    path("recipients/<int:pk>/", RecipientDetailView.as_view(), name="recipients_detail"),
    path("recipients/<int:pk>/edit/", RecipientUpdateView.as_view(), name="recipients_edit"),
    path("recipients/<int:pk>/delete/", RecipientDeleteView.as_view(), name="recipients_delete"),

    # Сообщения
    path("messages/", MessageListView.as_view(), name="messages_list"),
    path("messages/new/", MessageCreateView.as_view(), name="messages_create"),
    path("messages/<int:pk>/", MessageDetailView.as_view(), name="messages_detail"),
    path("messages/<int:pk>/edit/", MessageUpdateView.as_view(), name="messages_edit"),
    path("messages/<int:pk>/delete/", MessageDeleteView.as_view(), name="messages_delete"),

    # Рассылки (префикс mailings)
    path("mailings/", MailingListView.as_view(), name="mailings_list"),
    path("mailings/new/", MailingCreateView.as_view(), name="mailings_create"),
    path("mailings/<int:pk>/", MailingDetailView.as_view(), name="mailings_detail"),
    path("mailings/<int:pk>/edit/", MailingUpdateView.as_view(), name="mailings_edit"),
    path("mailings/<int:pk>/delete/", MailingDeleteView.as_view(), name="mailings_delete"),
    path("mailings/<int:pk>/send/", MailingSendView.as_view(), name="mailings_send"),
]
