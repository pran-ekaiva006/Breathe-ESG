from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status


from .filters import EmissionRecordFilter
from .models import EmissionRecord
from .serializers import EmissionRecordSerializer


class EmissionRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET  /api/emissions/             — paginated list with filtering & sorting
    GET  /api/emissions/{id}/        — single record detail
    POST /api/emissions/{id}/approve/ — approve a pending record (locks it)
    POST /api/emissions/{id}/reject/  — reject a pending record
    GET  /api/emissions/{id}/issues/ — validation issues for a specific record
    GET  /api/emissions/{id}/audits/ — audit log for a specific record
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

    # ── Approval workflow ─────────────────────────────────────────────────────

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        """
        POST /api/emissions/{id}/approve/

        Transitions approval_status → approved and sets locked=True.
        Rejected or locked records cannot be approved again.
        Creates an immutable AuditLog entry.
        """
        from audits.models import AuditLog

        record = self.get_object()

        if record.locked:
            return Response(
                {"error": "Record is locked and cannot be modified."},
                status=status.HTTP_409_CONFLICT,
            )

        if record.approval_status == EmissionRecord.ApprovalStatus.APPROVED:
            return Response(
                {"error": "Record is already approved."},
                status=status.HTTP_409_CONFLICT,
            )

        old_status = record.approval_status

        record.approval_status = EmissionRecord.ApprovalStatus.APPROVED
        record.locked = True
        record.save(update_fields=["approval_status", "locked"])

        AuditLog.objects.create(
            emission_record=record,
            action_type="STATUS_APPROVED",
            old_value={"approval_status": old_status, "locked": False},
            new_value={"approval_status": record.approval_status, "locked": True},
            changed_by=request.user if request.user.is_authenticated else None,
        )

        return Response(
            {
                "id": record.pk,
                "approval_status": record.approval_status,
                "locked": record.locked,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        """
        POST /api/emissions/{id}/reject/

        Transitions approval_status → rejected.
        Locked (already approved) records cannot be rejected.
        Accepts an optional JSON body: {"reason": "..."}.
        Creates an immutable AuditLog entry.
        """
        from audits.models import AuditLog

        record = self.get_object()

        if record.locked:
            return Response(
                {"error": "Record is locked and cannot be modified."},
                status=status.HTTP_409_CONFLICT,
            )

        if record.approval_status == EmissionRecord.ApprovalStatus.REJECTED:
            return Response(
                {"error": "Record is already rejected."},
                status=status.HTTP_409_CONFLICT,
            )

        old_status = record.approval_status
        reason = request.data.get("reason", "")

        record.approval_status = EmissionRecord.ApprovalStatus.REJECTED
        record.save(update_fields=["approval_status"])

        AuditLog.objects.create(
            emission_record=record,
            action_type="STATUS_REJECTED",
            old_value={"approval_status": old_status},
            new_value={"approval_status": record.approval_status, "reason": reason},
            changed_by=request.user if request.user.is_authenticated else None,
        )

        return Response(
            {
                "id": record.pk,
                "approval_status": record.approval_status,
                "locked": record.locked,
            },
            status=status.HTTP_200_OK,
        )

    # ── Sub-resource actions ──────────────────────────────────────────────────

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
