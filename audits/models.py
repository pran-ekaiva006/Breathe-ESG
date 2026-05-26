from django.conf import settings
from django.db import models

from emissions.models import EmissionRecord


class AuditLog(models.Model):
    """
    Immutable audit trail for changes made to emission records.
    Records should only ever be created (INSERT), never updated or deleted.
    """

    emission_record = models.ForeignKey(
        EmissionRecord,
        on_delete=models.CASCADE,
        related_name="audit_logs",
    )
    action_type = models.CharField(max_length=100)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["emission_record", "-timestamp"]),
            models.Index(fields=["changed_by"]),
            models.Index(fields=["action_type"]),
        ]

    def __str__(self):
        return f"{self.action_type} on Record #{self.emission_record_id} by {self.changed_by}"

    def save(self, *args, **kwargs):
        """Prevent updates — audit logs are write-once."""
        if self.pk:
            raise ValueError("AuditLog entries are immutable and cannot be updated.")
        super().save(*args, **kwargs)

