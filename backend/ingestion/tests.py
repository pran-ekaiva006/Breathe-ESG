import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient

from organizations.models import Organization
from ingestion.models import DataSource, UploadJob, RawRecord
from emissions.models import EmissionRecord
from validation_engine.models import ValidationIssue


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def org():
    return Organization.objects.create(name="Test Org")


@pytest.fixture
def sap_datasource(org):
    return DataSource.objects.create(
        organization=org,
        source_type="SAP",
        ingestion_method="csv"
    )

@pytest.fixture
def utility_datasource(org):
    return DataSource.objects.create(
        organization=org,
        source_type="UTILITY",
        ingestion_method="csv"
    )

@pytest.fixture
def travel_datasource(org):
    return DataSource.objects.create(
        organization=org,
        source_type="TRAVEL",
        ingestion_method="csv"
    )

@pytest.mark.django_db
def test_sap_upload_and_normalization(api_client, sap_datasource):
    csv_content = b"plant_code,fuel_type,quantity,unit,transaction_date\nPL01,Diesel,100,liters,2023-01-01"
    file = SimpleUploadedFile("sap.csv", csv_content, content_type="text/csv")
    
    url = reverse("ingestion:sap-upload")
    response = api_client.post(url, {"datasource_id": sap_datasource.id, "file": file}, format="multipart")
    
    assert response.status_code == 201
    job_id = response.data["upload_job_id"]
    
    norm_url = reverse("ingestion:sap-normalize", kwargs={"upload_job_id": job_id})
    norm_response = api_client.post(norm_url)
    assert norm_response.status_code == 200
    
    records = EmissionRecord.objects.all()
    assert records.count() == 1
    assert records[0].source_type == "SAP"
    assert records[0].value == 100

@pytest.mark.django_db
def test_utility_upload_and_normalization(api_client, utility_datasource):
    csv_content = b"meter_id,billing_start,billing_end,usage_kwh,tariff\nM01,2023-01-01,2023-01-31,500,0.15"
    file = SimpleUploadedFile("utility.csv", csv_content, content_type="text/csv")
    
    url = reverse("ingestion:utility-upload")
    response = api_client.post(url, {"datasource_id": utility_datasource.id, "file": file}, format="multipart")
    
    assert response.status_code == 201
    job_id = response.data["upload_job_id"]
    
    norm_url = reverse("ingestion:utility-normalize", kwargs={"upload_job_id": job_id})
    norm_response = api_client.post(norm_url)
    assert norm_response.status_code == 200
    
    records = EmissionRecord.objects.all()
    assert records.count() == 1
    assert records[0].source_type == "UTILITY"
    assert records[0].value == 500

@pytest.mark.django_db
def test_travel_upload_and_normalization(api_client, travel_datasource):
    csv_content = b"traveler_name,transport_type,departure_airport,arrival_airport,distance_km,trip_date\nJohn Doe,Flight,JFK,LHR,5500,2023-01-01"
    file = SimpleUploadedFile("travel.csv", csv_content, content_type="text/csv")
    
    url = reverse("ingestion:travel-upload")
    response = api_client.post(url, {"datasource_id": travel_datasource.id, "file": file}, format="multipart")
    
    assert response.status_code == 201
    job_id = response.data["upload_job_id"]
    
    norm_url = reverse("ingestion:travel-normalize", kwargs={"upload_job_id": job_id})
    norm_response = api_client.post(norm_url)
    assert norm_response.status_code == 200
    
    records = EmissionRecord.objects.all()
    assert records.count() == 1
    assert records[0].source_type == "TRAVEL"
    assert records[0].value == 5500

@pytest.mark.django_db
def test_validation_issue_creation(api_client, sap_datasource):
    # Missing required field 'transaction_date' and invalid quantity to trigger errors
    csv_content = b"plant_code,fuel_type,quantity,unit,transaction_date\nPL01,Diesel,-10,liters,2023-01-01"
    file = SimpleUploadedFile("sap_invalid.csv", csv_content, content_type="text/csv")
    
    url = reverse("ingestion:sap-upload")
    response = api_client.post(url, {"datasource_id": sap_datasource.id, "file": file}, format="multipart")
    assert response.status_code == 201
    job_id = response.data["upload_job_id"]
    
    norm_url = reverse("ingestion:sap-normalize", kwargs={"upload_job_id": job_id})
    norm_response = api_client.post(norm_url)
    assert norm_response.status_code == 200
    
    issues = ValidationIssue.objects.all()
    assert issues.count() > 0

