from django.urls import path
from .views import (
    HomeView, StatsView,
    RecipientListView, RecipientDetailView, RecipientCreateView, RecipientUpdateView, RecipientDeleteView,
    MessageListView, MessageDetailView, MessageCreateView, MessageUpdateView, MessageDeleteView,
    MailingListView, MailingDetailView, MailingCreateView, MailingUpdateView, MailingDeleteView, MailingSendView,
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("stats/", StatsView.as_view(), name="stats"),

    # Клиенты
    path("recipients/", RecipientListView.as_view(), name="recipients_list"),
    path("recipients/create/", RecipientCreateView.as_view(), name="recipients_create"),
    path("recipients/<int:pk>/", RecipientDetailView.as_view(), name="recipients_detail"),
    path("recipients/<int:pk>/edit/", RecipientUpdateView.as_view(), name="recipients_update"),
    path("recipients/<int:pk>/edit/", RecipientUpdateView.as_view(), name="recipients_edit"),
    path("recipients/<int:pk>/delete/", RecipientDeleteView.as_view(), name="recipients_delete"),


    # Сообщения
    path("messages/", MessageListView.as_view(), name="messages_list"),
    path("messages/new/", MessageCreateView.as_view(), name="messages_create"),
    path("messages/<int:pk>/delete/", MessageDeleteView.as_view(), name="messages_delete"),
    path("messages/<int:pk>/", MessageDetailView.as_view(), name="messages_detail"),
    path("messages/<int:pk>/edit/", MessageUpdateView.as_view(), name="messages_update"),
    path("messages/<int:pk>/edit/", MessageUpdateView.as_view(), name="messages_edit"),



    # Рассылки (префикс mailings)
    path("mailings/", MailingListView.as_view(), name="mailings_list"),
    path("mailings/new/", MailingCreateView.as_view(), name="mailings_create"),
    path("mailings/<int:pk>/", MailingDetailView.as_view(), name="mailings_detail"),
    path("mailings/<int:pk>/edit/", MailingUpdateView.as_view(), name="mailings_edit"),
    path("mailings/<int:pk>/delete/", MailingDeleteView.as_view(), name="mailings_delete"),
    path("mailings/<int:pk>/send/", MailingSendView.as_view(), name="mailings_send"),
]

