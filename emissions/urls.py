# pyrefly: ignore [missing-import]
from rest_framework.routers import DefaultRouter

from .views import EmissionRecordViewSet

router = DefaultRouter()
router.register(r"emissions", EmissionRecordViewSet, basename="emission")

app_name = "emissions"
urlpatterns = router.urls
