from rest_framework import serializers

from .models import ValidationIssue


class ValidationIssueSerializer(serializers.ModelSerializer):
    emission_record_id = serializers.IntegerField(read_only=True)
    severity_display = serializers.CharField(source="get_severity_display", read_only=True)

    class Meta:
        model = ValidationIssue
        fields = [
            "id",
            "emission_record_id",
            "issue_type",
            "severity",
            "severity_display",
            "message",
            "resolved",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
