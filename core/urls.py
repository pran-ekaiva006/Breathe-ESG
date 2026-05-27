"""
URL configuration for BreatheESG project.
"""

# pyrefly: ignore [missing-import]
from django.contrib import admin
# pyrefly: ignore [missing-import]
from django.urls import path, include

from .views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
    path("api/", include("ingestion.urls", namespace="ingestion")),
    path("api/", include("emissions.urls", namespace="emissions")),
    path("api/", include("validation_engine.urls", namespace="validation_engine")),
    path("api/", include("audits.urls", namespace="audits")),
]
