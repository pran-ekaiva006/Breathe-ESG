# pyrefly: ignore [missing-import]
from django.db import models

from organizations.models import Organization


class DataSource(models.Model):
    """A data source connected to an organization (e.g. SAP, utility bills)."""

    class SourceType(models.TextChoices):
        SAP = "SAP", "SAP"
        UTILITY = "UTILITY", "Utility"
        TRAVEL = "TRAVEL", "Travel"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="data_sources",
    )
    source_type = models.CharField(
        max_length=20,
        choices=SourceType.choices,
    )
    ingestion_method = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "source_type"]),
        ]

    def __str__(self):
        return f"{self.organization} — {self.get_source_type_display()}"


class UploadJob(models.Model):
    """Tracks an individual file upload against a data source."""

    class UploadStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    datasource = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name="upload_jobs",
    )
    file_name = models.CharField(max_length=255)
    upload_status = models.CharField(
        max_length=20,
        choices=UploadStatus.choices,
        default=UploadStatus.PENDING,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["upload_status"]),
            models.Index(fields=["uploaded_at"]),
        ]

    def __str__(self):
        return f"{self.file_name} ({self.get_upload_status_display()})"


class RawRecord(models.Model):
    """A single raw record extracted from an uploaded file."""

    class ProcessingStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        NORMALIZED = "normalized", "Normalized"
        FAILED = "failed", "Failed"

    upload_job = models.ForeignKey(
        UploadJob,
        on_delete=models.CASCADE,
        related_name="raw_records",
    )
    raw_payload = models.JSONField()
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
    )
    error_message = models.TextField(blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["processing_status"]),
        ]

    def __str__(self):
        return f"Record #{self.pk} — {self.get_processing_status_display()}"

