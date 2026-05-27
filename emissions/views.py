from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import EmissionRecordFilter
from .models import EmissionRecord
from .serializers import EmissionRecordSerializer


class EmissionRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/emissions/             — paginated list with filtering & sorting
    GET /api/emissions/{id}/        — single record detail
    GET /api/emissions/{id}/issues/ — validation issues for a specific record
    GET /api/emissions/{id}/audits/ — audit log for a specific record
    """

    serializer_class = EmissionRecordSerializer
    filterset_class = EmissionRecordFilter
    ordering_fields = ["record_date", "co2e_value", "created_at", "approval_status"]
    ordering = ["-record_date"]
    search_fields = ["activity_type", "organization__name"]

    def get_queryset(self):
        return (
            EmissionRecord.objects.select_related("organization")
            .prefetch_related("validation_issues", "audit_logs")
            .distinct()
        )

    @action(detail=True, url_path="issues")
    def issues(self, request, pk=None):
        """Return all ValidationIssues linked to this EmissionRecord."""
        from validation_engine.models import ValidationIssue
        from validation_engine.serializers import ValidationIssueSerializer

        record = self.get_object()
        issues = ValidationIssue.objects.filter(emission_record=record).order_by(
            "-created_at"
        )
        page = self.paginate_queryset(issues)
        if page is not None:
            return self.get_paginated_response(
                ValidationIssueSerializer(page, many=True).data
            )
        return Response(ValidationIssueSerializer(issues, many=True).data)

    @action(detail=True, url_path="audits")
    def audits(self, request, pk=None):
        """Return the audit log for this EmissionRecord."""
        from audits.models import AuditLog
        from audits.serializers import AuditLogSerializer

        record = self.get_object()
        logs = AuditLog.objects.filter(emission_record=record).order_by("-timestamp")
        page = self.paginate_queryset(logs)
        if page is not None:
            return self.get_paginated_response(
                AuditLogSerializer(page, many=True).data
            )
        return Response(AuditLogSerializer(logs, many=True).data)
