# pyrefly: ignore [missing-import]
from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    changed_by_username = serializers.CharField(
        source="changed_by.username", read_only=True, default=None
    )
    emission_record_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "emission_record_id",
            "action_type",
            "old_value",
            "new_value",
            "changed_by",
            "changed_by_username",
            "timestamp",
        ]
        read_only_fields = fields
