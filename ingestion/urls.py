from django.urls import path

from .views import sap_upload

app_name = "ingestion"

urlpatterns = [
    path("uploads/sap/", sap_upload, name="sap-upload"),
]

