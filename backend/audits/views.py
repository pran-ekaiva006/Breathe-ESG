# pyrefly: ignore [missing-import]
from rest_framework import viewsets

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/audit-logs/        — list audit entries with filtering & sorting
    GET /api/audit-logs/{id}/   — single audit entry detail
    """

    serializer_class = AuditLogSerializer
    filterset_fields = ["action_type", "changed_by", "emission_record"]
    ordering_fields = ["timestamp", "action_type"]
    ordering = ["-timestamp"]
    search_fields = ["action_type", "changed_by__username"]

    def get_queryset(self):
        return AuditLog.objects.select_related(
            "emission_record", "emission_record__organization", "changed_by"
        ).all()
