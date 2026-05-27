import csv
import io

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .models import DataSource, RawRecord, UploadJob
from .normalizer import normalize_sap_upload
from .travel_normalizer import normalize_travel_upload
from .utility_normalizer import normalize_utility_upload

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


@api_view(["POST"])
def normalize_sap_job(request, upload_job_id):
    """
    POST /api/uploads/sap/{upload_job_id}/normalize/

    Triggers normalization of all pending RawRecords for the given
    UploadJob, creating EmissionRecord rows and any ValidationIssues.
    """
    try:
        upload_job = UploadJob.objects.select_related(
            "datasource__organization"
        ).get(pk=upload_job_id, datasource__source_type=DataSource.SourceType.SAP)
    except UploadJob.DoesNotExist:
        return Response(
            {"error": f"SAP UploadJob with id={upload_job_id} not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if upload_job.upload_status != UploadJob.UploadStatus.COMPLETED:
        return Response(
            {
                "error": (
                    f"UploadJob is not in 'completed' state "
                    f"(current: {upload_job.upload_status}). "
                    "Upload must complete successfully before normalizing."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    summary = normalize_sap_upload(upload_job)

    return Response(
        {
            "upload_job_id": upload_job.pk,
            **summary,
        },
        status=status.HTTP_200_OK,
    )


# ── Utility Upload ─────────────────────────────────────────────────────────────

UTILITY_EXPECTED_COLUMNS = {"meter_id", "billing_start", "billing_end", "usage_kwh", "tariff"}

UTILITY_DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]


def _parse_date_utility(raw: str):
    from datetime import datetime
    for fmt in UTILITY_DATE_FORMATS:
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


@api_view(["POST"])
@parser_classes([MultiPartParser])
def utility_upload(request):
    """
    POST /api/uploads/utility/

    Accepts a CSV file for utility (electricity) billing data.
    Creates an UploadJob and stores each row as a RawRecord.

    Required form fields:
      - file         : the CSV file
      - datasource_id: ID of a DataSource with source_type=UTILITY
    """
    # ── 1. Validate required fields ───────────────────────────────────────────
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
        datasource = DataSource.objects.get(
            pk=datasource_id, source_type=DataSource.SourceType.UTILITY
        )
    except DataSource.DoesNotExist:
        return Response(
            {"error": f"DataSource id={datasource_id} with source_type=UTILITY not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # ── 3. Validate file type ─────────────────────────────────────────────────
    if not file_obj.name.endswith(".csv"):
        return Response(
            {"error": "Invalid file type. Only .csv files are accepted."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ── 4. Create UploadJob ───────────────────────────────────────────────────
    upload_job = UploadJob.objects.create(
        datasource=datasource,
        file_name=file_obj.name,
        upload_status=UploadJob.UploadStatus.PROCESSING,
    )

    # ── 5. Decode ─────────────────────────────────────────────────────────────
    try:
        decoded = file_obj.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        upload_job.upload_status = UploadJob.UploadStatus.FAILED
        upload_job.save()
        return Response(
            {"error": "File encoding not supported. Please upload a UTF-8 CSV."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    reader = csv.DictReader(io.StringIO(decoded))

    if not reader.fieldnames:
        upload_job.upload_status = UploadJob.UploadStatus.FAILED
        upload_job.save()
        return Response(
            {"error": "The CSV file is empty or has no header row."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ── 6. Parse rows ─────────────────────────────────────────────────────────
    rows_processed = 0
    rows_failed = 0
    errors = []
    raw_records_to_create = []

    for row_number, row in enumerate(reader, start=2):
        try:
            clean_row = {k.strip(): v.strip() for k, v in row.items() if k}

            if not any(clean_row.values()):
                continue

            row_errors = []

            # Validate billing period ─────────────────────────────────────────
            billing_start = _parse_date_utility(clean_row.get("billing_start", ""))
            billing_end = _parse_date_utility(clean_row.get("billing_end", ""))

            if billing_start is None:
                row_errors.append(
                    f"Invalid billing_start: '{clean_row.get('billing_start')}'."
                )
            if billing_end is None:
                row_errors.append(
                    f"Invalid billing_end: '{clean_row.get('billing_end')}'."
                )
            if billing_start and billing_end and billing_end <= billing_start:
                row_errors.append(
                    f"billing_end ({billing_end}) must be after billing_start ({billing_start})."
                )

            # Validate usage_kwh ──────────────────────────────────────────────
            raw_usage = clean_row.get("usage_kwh", "")
            try:
                usage = float(raw_usage.replace(",", "")) if raw_usage else None
                if usage is None:
                    row_errors.append("Missing 'usage_kwh'.")
                elif usage < 0:
                    row_errors.append(f"Negative 'usage_kwh' ({usage}) is not allowed.")
            except ValueError:
                row_errors.append(f"Non-numeric 'usage_kwh': '{raw_usage}'.")

            if row_errors:
                rows_failed += 1
                errors.append({"row": row_number, "errors": row_errors})
                # Preserve the raw row even on failure for traceability
                raw_records_to_create.append(
                    RawRecord(
                        upload_job=upload_job,
                        raw_payload={**clean_row, "_row_errors": row_errors},
                        processing_status=RawRecord.ProcessingStatus.FAILED,
                        error_message=" | ".join(row_errors),
                    )
                )
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

    # ── 7. Bulk insert ────────────────────────────────────────────────────────
    if raw_records_to_create:
        RawRecord.objects.bulk_create(raw_records_to_create)

    # ── 8. Finalise status ────────────────────────────────────────────────────
    if rows_processed == 0 and rows_failed == 0:
        upload_job.upload_status = UploadJob.UploadStatus.FAILED
        upload_job.save()
        return Response(
            {"error": "The CSV contained no data rows."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    upload_job.upload_status = (
        UploadJob.UploadStatus.FAILED
        if rows_processed == 0
        else UploadJob.UploadStatus.COMPLETED
    )
    upload_job.save()

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


@api_view(["POST"])
def normalize_utility_job(request, upload_job_id):
    """
    POST /api/uploads/utility/{upload_job_id}/normalize/

    Triggers normalization of all pending RawRecords for the given
    UTILITY UploadJob, creating EmissionRecord rows (Scope 2) and
    any ValidationIssues for spikes or invalid data.
    """
    try:
        upload_job = UploadJob.objects.select_related(
            "datasource__organization"
        ).get(pk=upload_job_id, datasource__source_type=DataSource.SourceType.UTILITY)
    except UploadJob.DoesNotExist:
        return Response(
            {"error": f"UTILITY UploadJob with id={upload_job_id} not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if upload_job.upload_status != UploadJob.UploadStatus.COMPLETED:
        return Response(
            {
                "error": (
                    f"UploadJob is not in 'completed' state "
                    f"(current: {upload_job.upload_status}). "
                    "Upload must complete successfully before normalizing."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    summary = normalize_utility_upload(upload_job)

    return Response(
        {
            "upload_job_id": upload_job.pk,
            **summary,
        },
        status=status.HTTP_200_OK,
    )


# ── Travel Upload ─────────────────────────────────────────────────────────

TRAVEL_EXPECTED_COLUMNS = {
    "traveler_name", "transport_type", "departure_airport",
    "arrival_airport", "distance_km", "trip_date",
}

TRAVEL_DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]


def _parse_date_travel(raw: str):
    from datetime import datetime
    for fmt in TRAVEL_DATE_FORMATS:
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


@api_view(["POST"])
@parser_classes([MultiPartParser])
def travel_upload(request):
    """
    POST /api/uploads/travel/

    Accepts a CSV file for business travel data.
    Creates an UploadJob and stores each row as a RawRecord.

    Required form fields:
      - file         : the CSV file
      - datasource_id: ID of a DataSource with source_type=TRAVEL
    """
    # ── 1. Validate required fields ───────────────────────────────────────────
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
        datasource = DataSource.objects.get(
            pk=datasource_id, source_type=DataSource.SourceType.TRAVEL
        )
    except DataSource.DoesNotExist:
        return Response(
            {"error": f"DataSource id={datasource_id} with source_type=TRAVEL not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # ── 3. Validate file type ─────────────────────────────────────────────────
    if not file_obj.name.endswith(".csv"):
        return Response(
            {"error": "Invalid file type. Only .csv files are accepted."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ── 4. Create UploadJob ───────────────────────────────────────────────────
    upload_job = UploadJob.objects.create(
        datasource=datasource,
        file_name=file_obj.name,
        upload_status=UploadJob.UploadStatus.PROCESSING,
    )

    # ── 5. Decode ───────────────────────────────────────────────────────────
    try:
        decoded = file_obj.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        upload_job.upload_status = UploadJob.UploadStatus.FAILED
        upload_job.save()
        return Response(
            {"error": "File encoding not supported. Please upload a UTF-8 CSV."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    reader = csv.DictReader(io.StringIO(decoded))

    if not reader.fieldnames:
        upload_job.upload_status = UploadJob.UploadStatus.FAILED
        upload_job.save()
        return Response(
            {"error": "The CSV file is empty or has no header row."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ── 6. Parse rows ─────────────────────────────────────────────────────────
    rows_processed = 0
    rows_failed = 0
    errors = []
    raw_records_to_create = []

    for row_number, row in enumerate(reader, start=2):
        try:
            clean_row = {k.strip(): v.strip() for k, v in row.items() if k}

            if not any(clean_row.values()):
                continue

            row_errors = []

            # Validate airport codes ──────────────────────────────────────────
            dep = clean_row.get("departure_airport", "").strip()
            arr = clean_row.get("arrival_airport", "").strip()
            if not dep:
                row_errors.append("Missing 'departure_airport'.")
            if not arr:
                row_errors.append("Missing 'arrival_airport'.")
            if dep and arr and dep.upper() == arr.upper():
                row_errors.append(
                    f"'departure_airport' and 'arrival_airport' are the same ({dep})."
                )

            # Validate distance_km ────────────────────────────────────────────
            raw_dist = clean_row.get("distance_km", "")
            try:
                distance = float(raw_dist.replace(",", "")) if raw_dist else None
                if distance is None:
                    row_errors.append("Missing 'distance_km'.")
                elif distance <= 0:
                    row_errors.append(
                        f"'distance_km' must be positive (got {distance})."
                    )
            except ValueError:
                row_errors.append(f"Non-numeric 'distance_km': '{raw_dist}'.")

            # Validate trip_date ──────────────────────────────────────────────
            raw_date = clean_row.get("trip_date", "")
            trip_date = _parse_date_travel(raw_date)
            if trip_date is None:
                row_errors.append(f"Invalid or missing 'trip_date': '{raw_date}'.")

            if row_errors:
                rows_failed += 1
                errors.append({"row": row_number, "errors": row_errors})
                raw_records_to_create.append(
                    RawRecord(
                        upload_job=upload_job,
                        raw_payload={**clean_row, "_row_errors": row_errors},
                        processing_status=RawRecord.ProcessingStatus.FAILED,
                        error_message=" | ".join(row_errors),
                    )
                )
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

    # ── 7. Bulk insert ────────────────────────────────────────────────────────
    if raw_records_to_create:
        RawRecord.objects.bulk_create(raw_records_to_create)

    # ── 8. Finalise status ────────────────────────────────────────────────────
    if rows_processed == 0 and rows_failed == 0:
        upload_job.upload_status = UploadJob.UploadStatus.FAILED
        upload_job.save()
        return Response(
            {"error": "The CSV contained no data rows."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    upload_job.upload_status = (
        UploadJob.UploadStatus.FAILED
        if rows_processed == 0
        else UploadJob.UploadStatus.COMPLETED
    )
    upload_job.save()

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


@api_view(["POST"])
def normalize_travel_job(request, upload_job_id):
    """
    POST /api/uploads/travel/{upload_job_id}/normalize/

    Triggers normalization of all pending RawRecords for the given
    TRAVEL UploadJob, creating EmissionRecord rows (Scope 3) and
    any ValidationIssues for impossible distances or missing fields.
    """
    try:
        upload_job = UploadJob.objects.select_related(
            "datasource__organization"
        ).get(pk=upload_job_id, datasource__source_type=DataSource.SourceType.TRAVEL)
    except UploadJob.DoesNotExist:
        return Response(
            {"error": f"TRAVEL UploadJob with id={upload_job_id} not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if upload_job.upload_status != UploadJob.UploadStatus.COMPLETED:
        return Response(
            {
                "error": (
                    f"UploadJob is not in 'completed' state "
                    f"(current: {upload_job.upload_status}). "
                    "Upload must complete successfully before normalizing."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    summary = normalize_travel_upload(upload_job)

    return Response(
        {
            "upload_job_id": upload_job.pk,
            **summary,
        },
        status=status.HTTP_200_OK,
    )
