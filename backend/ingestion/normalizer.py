"""
SAP Normalization Service
=========================
Reads RawRecord rows from a given UploadJob and normalizes them
into EmissionRecord rows. Creates ValidationIssue records for
suspicious or invalid data.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from emissions.models import EmissionRecord
from organizations.models import Organization
from validation_engine.models import ValidationIssue

from .models import RawRecord

# ── Unit normalization map ────────────────────────────────────────────────────
UNIT_MAP = {
    # Liters
    "liters": "L",
    "liter": "L",
    "litre": "L",
    "litres": "L",
    "l": "L",
    # Gallons
    "gallon": "GAL",
    "gallons": "GAL",
    "gal": "GAL",
    # Kilograms
    "kg": "KG",
    "kilogram": "KG",
    "kilograms": "KG",
    # Cubic metres
    "m3": "M3",
    "cubic meter": "M3",
    "cubic metre": "M3",
    # kWh
    "kwh": "KWH",
    "kilowatt-hour": "KWH",
    "kilowatt hour": "KWH",
}

# Placeholder emission factor — real factors would come from a reference table
DEFAULT_EMISSION_FACTOR = Decimal("0.233")

# Date formats we try to parse
DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
]


def _normalize_unit(raw_unit: str) -> tuple[str, bool]:
    """
    Return (normalized_unit, is_known).
    is_known=False means the unit was not in our map.
    """
    normalized = UNIT_MAP.get(raw_unit.strip().lower())
    return (normalized or raw_unit.upper(), normalized is not None)


def _parse_date(raw_date: str):
    """Try multiple date formats. Returns a date object or None."""
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw_date.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


def _parse_decimal(raw_value: str):
    """Return a Decimal or None for invalid/missing values."""
    if not raw_value or not raw_value.strip():
        return None
    try:
        return Decimal(raw_value.strip().replace(",", ""))
    except InvalidOperation:
        return None


# ── Main service function ─────────────────────────────────────────────────────

def normalize_sap_upload(upload_job) -> dict:
    """
    Process all pending RawRecords for the given UploadJob.

    Returns a summary dict:
      {
        "records_normalized": int,
        "records_failed": int,
        "validation_issues_created": int,
      }
    """
    organization: Organization = upload_job.datasource.organization
    pending_records = RawRecord.objects.filter(
        upload_job=upload_job,
        processing_status=RawRecord.ProcessingStatus.PENDING,
    )

    records_normalized = 0
    records_failed = 0
    validation_issues_to_create = []

    for raw in pending_records:
        payload: dict = raw.raw_payload
        errors = []
        warnings = []

        # ── Map: fuel_type → activity_type ───────────────────────────────────
        activity_type = payload.get("fuel_type", "").strip()
        if not activity_type:
            errors.append("Missing 'fuel_type' field.")

        # ── Map: quantity → value ─────────────────────────────────────────────
        raw_quantity = payload.get("quantity", "")
        value = _parse_decimal(raw_quantity)
        if value is None:
            errors.append(f"Invalid or missing 'quantity': '{raw_quantity}'.")
        elif value <= 0:
            warnings.append(f"Quantity is zero or negative ({value}). Possibly erroneous.")

        # ── Map: transaction_date → record_date ──────────────────────────────
        raw_date = payload.get("transaction_date", "")
        record_date = _parse_date(raw_date)
        if record_date is None:
            errors.append(f"Invalid or missing 'transaction_date': '{raw_date}'.")

        # ── Normalize unit ────────────────────────────────────────────────────
        raw_unit = payload.get("unit", "")
        normalized_unit, unit_known = _normalize_unit(raw_unit)
        if not unit_known:
            warnings.append(f"Unknown unit '{raw_unit}' — stored as '{normalized_unit}'.")

        # ── Hard errors → mark raw record as failed ───────────────────────────
        if errors:
            raw.processing_status = RawRecord.ProcessingStatus.FAILED
            raw.error_message = " | ".join(errors)
            raw.save(update_fields=["processing_status", "error_message"])
            records_failed += 1
            # Still create a HIGH ValidationIssue for traceability
            for msg in errors:
                validation_issues_to_create.append(
                    _make_issue(
                        emission_record=None,
                        raw_record=raw,
                        issue_type="NORMALIZATION_ERROR",
                        severity=ValidationIssue.Severity.HIGH,
                        message=msg,
                    )
                )
            continue

        # ── Create EmissionRecord ─────────────────────────────────────────────
        co2e_value = (value * DEFAULT_EMISSION_FACTOR).quantize(Decimal("0.000001"))

        emission_record = EmissionRecord.objects.create(
            organization=organization,
            source_type=EmissionRecord.SourceType.SAP,
            scope_category=EmissionRecord.ScopeCategory.SCOPE_1,  # SAP = direct/Scope 1
            activity_type=activity_type,
            value=value,
            unit=raw_unit or normalized_unit,
            normalized_unit=normalized_unit,
            co2e_value=co2e_value,
            emission_factor=DEFAULT_EMISSION_FACTOR,
            record_date=record_date,
            approval_status=EmissionRecord.ApprovalStatus.PENDING,
            locked=False,
        )

        # ── Soft warnings → LOW/MEDIUM ValidationIssues ───────────────────────
        for msg in warnings:
            severity = (
                ValidationIssue.Severity.MEDIUM
                if "zero or negative" in msg
                else ValidationIssue.Severity.LOW
            )
            validation_issues_to_create.append(
                ValidationIssue(
                    emission_record=emission_record,
                    issue_type="DATA_WARNING",
                    severity=severity,
                    message=msg,
                )
            )

        # ── Mark RawRecord as normalized ──────────────────────────────────────
        raw.processing_status = RawRecord.ProcessingStatus.NORMALIZED
        raw.save(update_fields=["processing_status"])
        records_normalized += 1

    # ── Bulk create all ValidationIssues (skip the ones with no EmissionRecord) ──
    real_issues = [v for v in validation_issues_to_create if v.emission_record_id is not None]
    ValidationIssue.objects.bulk_create(real_issues)

    return {
        "records_normalized": records_normalized,
        "records_failed": records_failed,
        "validation_issues_created": len(real_issues),
    }


# ── Helper ────────────────────────────────────────────────────────────────────

def _make_issue(emission_record, raw_record, issue_type, severity, message):
    """Build a ValidationIssue; emission_record may be None for hard failures."""
    return ValidationIssue(
        emission_record=emission_record,
        issue_type=issue_type,
        severity=severity,
        message=f"RawRecord #{raw_record.pk}: {message}",
    )
