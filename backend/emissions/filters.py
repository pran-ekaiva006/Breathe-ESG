import django_filters

from .models import EmissionRecord


class EmissionRecordFilter(django_filters.FilterSet):
    """Filter set for the EmissionRecord list endpoint."""

    # Exact matches
    source_type = django_filters.ChoiceFilter(choices=EmissionRecord.SourceType.choices)
    scope_category = django_filters.ChoiceFilter(choices=EmissionRecord.ScopeCategory.choices)
    approval_status = django_filters.ChoiceFilter(choices=EmissionRecord.ApprovalStatus.choices)
    locked = django_filters.BooleanFilter()
    organization = django_filters.NumberFilter(field_name="organization_id")

    # Date range
    record_date_from = django_filters.DateFilter(field_name="record_date", lookup_expr="gte")
    record_date_to = django_filters.DateFilter(field_name="record_date", lookup_expr="lte")

    # CO2e range
    co2e_min = django_filters.NumberFilter(field_name="co2e_value", lookup_expr="gte")
    co2e_max = django_filters.NumberFilter(field_name="co2e_value", lookup_expr="lte")

    # Filter by linked validation issue severity
    validation_severity = django_filters.ChoiceFilter(
        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")],
        field_name="validation_issues__severity",
        lookup_expr="exact",
    )

    class Meta:
        model = EmissionRecord
        fields = [
            "source_type",
            "scope_category",
            "approval_status",
            "locked",
            "organization",
            "record_date_from",
            "record_date_to",
            "co2e_min",
            "co2e_max",
            "validation_severity",
        ]
