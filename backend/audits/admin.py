# pyrefly: ignore [missing-import]
from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("emission_record", "action_type", "changed_by", "timestamp")
    list_filter = ("action_type",)
    search_fields = ("action_type", "changed_by__username")
    readonly_fields = (
        "emission_record",
        "action_type",
        "old_value",
        "new_value",
        "changed_by",
        "timestamp",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

