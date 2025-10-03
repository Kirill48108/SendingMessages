from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # ... existing code ...
    path('', include('users.urls')),
    path('', include('sendingmessages.urls')),
]
