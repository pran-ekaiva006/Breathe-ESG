# pyrefly: ignore [missing-import]
from rest_framework.routers import DefaultRouter

from .views import AuditLogViewSet

router = DefaultRouter()
router.register(r"audit-logs", AuditLogViewSet, basename="audit-log")

app_name = "audits"
urlpatterns = router.urls
