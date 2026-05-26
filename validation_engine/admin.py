from django.contrib import admin

from .models import ValidationIssue


@admin.register(ValidationIssue)
class ValidationIssueAdmin(admin.ModelAdmin):
    list_display = ("emission_record", "issue_type", "severity", "resolved", "created_at")
    list_filter = ("severity", "resolved")
    search_fields = ("issue_type", "message")

