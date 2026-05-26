from django.contrib import admin

from .models import Organization, UserOrganization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "industry", "created_at", "updated_at")
    search_fields = ("name", "industry")


@admin.register(UserOrganization)
class UserOrganizationAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "role")
    list_filter = ("role",)
    search_fields = ("user__username", "organization__name")

