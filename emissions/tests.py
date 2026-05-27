import pytest
from rest_framework.test import APIClient
from decimal import Decimal

from organizations.models import Organization
from emissions.models import EmissionRecord
from audits.models import AuditLog


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def org():
    return Organization.objects.create(name="Test Org")


@pytest.fixture
def emission_record(org):
    return EmissionRecord.objects.create(
        organization=org,
        source_type="SAP",
        scope_category="Scope 1",
        activity_type="Diesel",
        value=Decimal("100.0"),
        unit="L",
        normalized_unit="L",
        co2e_value=Decimal("23.3"),
        emission_factor=Decimal("0.233"),
        record_date="2023-01-01",
        approval_status="pending",
        locked=False
    )


@pytest.mark.django_db
def test_approval_workflow(api_client, emission_record):
    url = f"/api/emissions/{emission_record.id}/approve/"
    response = api_client.post(url)
    
    assert response.status_code == 200
    emission_record.refresh_from_db()
    assert emission_record.approval_status == "approved"
    assert emission_record.locked is True
    
    audits = AuditLog.objects.filter(emission_record=emission_record)
    assert audits.count() == 1
    assert audits[0].action_type == "STATUS_APPROVED"


@pytest.mark.django_db
def test_rejection_workflow(api_client, emission_record):
    url = f"/api/emissions/{emission_record.id}/reject/"
    response = api_client.post(url, {"reason": "Data incorrect"}, format="json")
    
    assert response.status_code == 200
    emission_record.refresh_from_db()
    assert emission_record.approval_status == "rejected"
    assert emission_record.locked is False
    
    audits = AuditLog.objects.filter(emission_record=emission_record)
    assert audits.count() == 1
    assert audits[0].action_type == "STATUS_REJECTED"


@pytest.mark.django_db
def test_locked_record_protection(api_client, emission_record):
    # Approve first to lock it
    url_approve = f"/api/emissions/{emission_record.id}/approve/"
    api_client.post(url_approve)
    emission_record.refresh_from_db()
    assert emission_record.locked is True
    
    # Try to reject a locked record
    url_reject = f"/api/emissions/{emission_record.id}/reject/"
    response = api_client.post(url_reject, {"reason": "Late rejection"}, format="json")
    
    assert response.status_code == 409
    assert "locked" in response.data["error"].lower()
    
    # Try to approve again
    response_approve2 = api_client.post(url_approve)
    assert response_approve2.status_code == 409
