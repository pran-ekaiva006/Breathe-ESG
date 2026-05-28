# pyrefly: ignore [missing-import]
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ValidationIssueViewSet

app_name = "validation_engine"

router = DefaultRouter()
router.register(r"validation-issues", ValidationIssueViewSet, basename="validation-issue")

urlpatterns = [
    path("", include(router.urls)),
]
