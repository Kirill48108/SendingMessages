from django.contrib import admin

from .models import UserProfile, Recipient, Message, Mailing, MailingAttempt

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "is_blocked")
    list_filter = ("role", "is_blocked")
    search_fields = ("user__username", "user__email")
    actions = ["block_users", "unblock_users"]

    def block_users(self, request, queryset):
        queryset.update(is_blocked=True)
    block_users.short_description = "Заблокировать выбранных пользователей"

    def unblock_users(self, request, queryset):
        queryset.update(is_blocked=False)
    unblock_users.short_description = "Разблокировать выбранных пользователей"


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "owner")
    search_fields = ("full_name", "email", "comment", "owner__username")
    list_filter = ("owner",)
    list_per_page = 25



@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "owner")
    search_fields = ("subject", "body", "owner__username")
    list_filter = ("owner",)
    list_per_page = 25



@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("message", "status", "start_at", "end_at", "owner", "is_disabled")
    list_filter = ("status", "owner", "is_disabled")
    search_fields = ("message__subject", "owner__username")
    filter_horizontal = ("recipients",)
    date_hierarchy = "start_at"
    actions = ["disable_mailings", "enable_mailings"]

    def disable_mailings(self, request, queryset):
        queryset.update(is_disabled=True)
    disable_mailings.short_description = "Отключить выбранные рассылки"

    def enable_mailings(self, request, queryset):
        queryset.update(is_disabled=False)
    enable_mailings.short_description = "Включить выбранные рассылки"



@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = ("mailing", "status", "attempted_at")
    list_filter = ("status", "mailing")
    search_fields = ("mailing__message__subject", "server_response")
    date_hierarchy = "attempted_at"
    list_per_page = 25

