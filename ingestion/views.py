import csv
import io

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .models import DataSource, RawRecord, UploadJob

# Columns we expect in a SAP CSV upload
SAP_EXPECTED_COLUMNS = {"plant_code", "fuel_type", "quantity", "unit", "transaction_date"}


@api_view(["POST"])
@parser_classes([MultiPartParser])
def sap_upload(request):
    """
    POST /api/uploads/sap/

    Accepts a CSV file upload for SAP source data.
    Creates an UploadJob and stores each row as a RawRecord.

    Required form fields:
      - file         : the CSV file
      - datasource_id: ID of an existing DataSource (source_type=SAP)
    """

    # ── 1. Validate presence of required form fields ──────────────────────────
    file_obj = request.FILES.get("file")
    datasource_id = request.data.get("datasource_id")

    if not file_obj:
        return Response(
            {"error": "No file provided. Send a CSV as 'file' in multipart form."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not datasource_id:
        return Response(
            {"error": "'datasource_id' field is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ── 2. Resolve DataSource ─────────────────────────────────────────────────
    try:
        datasource = DataSource.objects.get(pk=datasource_id, source_type=DataSource.SourceType.SAP)
    except DataSource.DoesNotExist:
        return Response(
            {"error": f"DataSource with id={datasource_id} and source_type=SAP not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # ── 3. Validate file type ─────────────────────────────────────────────────
    if not file_obj.name.endswith(".csv"):
        return Response(
            {"error": "Invalid file type. Only .csv files are accepted."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ── 4. Create UploadJob (status=pending) ──────────────────────────────────
    upload_job = UploadJob.objects.create(
        datasource=datasource,
        file_name=file_obj.name,
        upload_status=UploadJob.UploadStatus.PROCESSING,
    )

    # ── 5. Parse CSV ──────────────────────────────────────────────────────────
    rows_processed = 0
    rows_failed = 0
    errors = []

    try:
        decoded = file_obj.read().decode("utf-8-sig")  # utf-8-sig strips BOM if present
    except UnicodeDecodeError:
        upload_job.upload_status = UploadJob.UploadStatus.FAILED
        upload_job.save()
        return Response(
            {"error": "File encoding is not supported. Please upload a UTF-8 CSV."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    reader = csv.DictReader(io.StringIO(decoded))

    # Check for empty file / missing header
    if not reader.fieldnames:
        upload_job.upload_status = UploadJob.UploadStatus.FAILED
        upload_job.save()
        return Response(
            {"error": "The uploaded CSV file is empty or has no header row."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    raw_records_to_create = []

    for row_number, row in enumerate(reader, start=2):  # start=2: row 1 is the header
        try:
            # Strip whitespace from keys and values
            clean_row = {k.strip(): v.strip() for k, v in row.items() if k}

            # Skip fully empty rows
            if not any(clean_row.values()):
                continue

            raw_records_to_create.append(
                RawRecord(
                    upload_job=upload_job,
                    raw_payload=clean_row,
                    processing_status=RawRecord.ProcessingStatus.PENDING,
                )
            )
            rows_processed += 1

        except Exception as exc:
            rows_failed += 1
            errors.append({"row": row_number, "error": str(exc)})

    # ── 6. Bulk insert RawRecords ─────────────────────────────────────────────
    if raw_records_to_create:
        RawRecord.objects.bulk_create(raw_records_to_create)

    # ── 7. Finalise UploadJob status ──────────────────────────────────────────
    if rows_processed == 0 and rows_failed == 0:
        upload_job.upload_status = UploadJob.UploadStatus.FAILED
        upload_job.save()
        return Response(
            {"error": "The CSV contained no data rows."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if rows_failed > 0 and rows_processed == 0:
        upload_job.upload_status = UploadJob.UploadStatus.FAILED
    else:
        upload_job.upload_status = UploadJob.UploadStatus.COMPLETED

    upload_job.save()

    # ── 8. Return summary ─────────────────────────────────────────────────────
    return Response(
        {
            "upload_job_id": upload_job.pk,
            "file_name": upload_job.file_name,
            "upload_status": upload_job.upload_status,
            "rows_processed": rows_processed,
            "rows_failed": rows_failed,
            "errors": errors,
        },
        status=status.HTTP_201_CREATED,
    )
