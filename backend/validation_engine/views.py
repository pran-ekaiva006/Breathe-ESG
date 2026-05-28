from rest_framework import viewsets

from .models import ValidationIssue
from .serializers import ValidationIssueSerializer


class ValidationIssueViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/validation-issues/        — list with filtering & sorting
    GET /api/validation-issues/{id}/   — single issue detail
    """

    serializer_class = ValidationIssueSerializer
    filterset_fields = ["severity", "resolved", "issue_type"]
    ordering_fields = ["severity", "created_at", "resolved"]
    ordering = ["-created_at"]
    search_fields = ["message", "issue_type"]

    def get_queryset(self):
        return ValidationIssue.objects.select_related(
            "emission_record", "emission_record__organization"
        ).all()
