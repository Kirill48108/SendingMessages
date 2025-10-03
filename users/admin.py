from django.contrib import admin
from .models import UserProfile, EmailConfirmation

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "is_blocked")
    list_filter = ("role", "is_blocked")
    search_fields = ("user__username", "user__email")

@admin.register(EmailConfirmation)
class EmailConfirmationAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "created_at", "is_used")
    list_filter = ("is_used",)
    search_fields = ("user__username", "user__email", "token")
