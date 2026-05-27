from django.urls import path

from .views import (
    normalize_sap_job,
    normalize_travel_job,
    normalize_utility_job,
    sap_upload,
    travel_upload,
    utility_upload,
)

app_name = "ingestion"

urlpatterns = [
    path("uploads/sap/", sap_upload, name="sap-upload"),
    path("uploads/sap/<int:upload_job_id>/normalize/", normalize_sap_job, name="sap-normalize"),
    path("uploads/utility/", utility_upload, name="utility-upload"),
    path("uploads/utility/<int:upload_job_id>/normalize/", normalize_utility_job, name="utility-normalize"),
    path("uploads/travel/", travel_upload, name="travel-upload"),
    path("uploads/travel/<int:upload_job_id>/normalize/", normalize_travel_job, name="travel-normalize"),
]


