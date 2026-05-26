from django.db import models

from emissions.models import EmissionRecord


class ValidationIssue(models.Model):
    """A flagged issue on an emission record for review."""

    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    emission_record = models.ForeignKey(
        EmissionRecord,
        on_delete=models.CASCADE,
        related_name="validation_issues",
    )
    issue_type = models.CharField(max_length=100)
    severity = models.CharField(
        max_length=10,
        choices=Severity.choices,
    )
    message = models.TextField()
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["severity"]),
            models.Index(fields=["resolved"]),
            models.Index(fields=["emission_record", "resolved"]),
        ]

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.issue_type} — Record #{self.emission_record_id}"

