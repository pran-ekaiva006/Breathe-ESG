from rest_framework.routers import DefaultRouter

from .views import ValidationIssueViewSet

router = DefaultRouter()
router.register(r"validation-issues", ValidationIssueViewSet, basename="validation-issue")

app_name = "validation_engine"
urlpatterns = router.urls
