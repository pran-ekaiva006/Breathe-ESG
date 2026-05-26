from django.contrib import admin

from .models import DataSource, RawRecord, UploadJob


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ("organization", "source_type", "ingestion_method", "created_at")
    list_filter = ("source_type",)
    search_fields = ("organization__name",)


@admin.register(UploadJob)
class UploadJobAdmin(admin.ModelAdmin):
    list_display = ("file_name", "datasource", "upload_status", "uploaded_at")
    list_filter = ("upload_status",)
    search_fields = ("file_name",)


@admin.register(RawRecord)
class RawRecordAdmin(admin.ModelAdmin):
    list_display = ("pk", "upload_job", "processing_status")
    list_filter = ("processing_status",)

