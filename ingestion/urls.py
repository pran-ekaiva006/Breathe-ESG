from django.urls import path

from .views import normalize_sap_job, sap_upload, utility_upload

app_name = "ingestion"

urlpatterns = [
    path("uploads/sap/", sap_upload, name="sap-upload"),
    path("uploads/sap/<int:upload_job_id>/normalize/", normalize_sap_job, name="sap-normalize"),
    path("uploads/utility/", utility_upload, name="utility-upload"),
]

