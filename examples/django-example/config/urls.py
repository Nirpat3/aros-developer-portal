from django.contrib import admin
from django.urls import path, include
from dashboard.views import dashboard_view, event_log_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", dashboard_view, name="dashboard"),
    path("events/", event_log_view, name="event_log"),
]
