from django.contrib import admin

from .models import EmissionRecord


@admin.register(EmissionRecord)
class EmissionRecordAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "scope_category",
        "source_type",
        "activity_type",
        "co2e_value",
        "approval_status",
        "locked",
        "record_date",
    )
    list_filter = ("scope_category", "source_type", "approval_status", "locked")
    search_fields = ("organization__name", "activity_type")
    date_hierarchy = "record_date"

