from rest_framework import serializers

from .models import EmissionRecord


class EmissionRecordSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )

    class Meta:
        model = EmissionRecord
        fields = [
            "id",
            "organization",
            "organization_name",
            "source_type",
            "scope_category",
            "activity_type",
            "value",
            "unit",
            "normalized_unit",
            "co2e_value",
            "emission_factor",
            "record_date",
            "approval_status",
            "locked",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "organization_name"]
