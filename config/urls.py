from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("users/", include(("users.urls", "users"), namespace="users")),
    path("", include("sendingmessages.urls")),
    path("dashboard/", RedirectView.as_view(pattern_name="users:manager_dashboard", permanent=False)),
]

