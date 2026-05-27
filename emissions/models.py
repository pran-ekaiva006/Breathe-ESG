# pyrefly: ignore [missing-import]
from django.db import models

from organizations.models import Organization


class EmissionRecord(models.Model):
    """A normalized emission record tied to an organization."""

    class SourceType(models.TextChoices):
        SAP = "SAP", "SAP"
        UTILITY = "UTILITY", "Utility"
        TRAVEL = "TRAVEL", "Travel"

    class ScopeCategory(models.TextChoices):
        SCOPE_1 = "Scope 1", "Scope 1"
        SCOPE_2 = "Scope 2", "Scope 2"
        SCOPE_3 = "Scope 3", "Scope 3"

    class ApprovalStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="emission_records",
    )
    source_type = models.CharField(
        max_length=20,
        choices=SourceType.choices,
    )
    scope_category = models.CharField(
        max_length=10,
        choices=ScopeCategory.choices,
    )
    activity_type = models.CharField(max_length=255)
    value = models.DecimalField(max_digits=20, decimal_places=6)
    unit = models.CharField(max_length=50)
    normalized_unit = models.CharField(max_length=50)
    co2e_value = models.DecimalField(max_digits=20, decimal_places=6)
    emission_factor = models.DecimalField(max_digits=20, decimal_places=10)
    record_date = models.DateField()
    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )
    locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "scope_category"]),
            models.Index(fields=["source_type"]),
            models.Index(fields=["approval_status"]),
            models.Index(fields=["record_date"]),
            models.Index(fields=["locked"]),
        ]

    def __str__(self):
        return (
            f"{self.organization} | {self.scope_category} | "
            f"{self.activity_type} — {self.co2e_value} tCO2e"
        )

