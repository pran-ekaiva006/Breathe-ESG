"""
Utility Normalization Service
==============================
Reads pending RawRecord rows from a UTILITY UploadJob and normalizes
them into EmissionRecord rows (Scope 2 — indirect electricity).

Creates ValidationIssue records for:
  - negative usage
  - abnormal spikes (usage > spike threshold)
  - billing_end before or equal to billing_start
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from emissions.models import EmissionRecord
from validation_engine.models import ValidationIssue

from .models import RawRecord

# ── Constants ─────────────────────────────────────────────────────────────────

# UK/EU average grid emission factor for electricity (kgCO2e per kWh)
# This would come from a reference table in production.
ELECTRICITY_EMISSION_FACTOR = Decimal("0.23314")

# Spike threshold: flag any single record with usage above this (kWh)
# Represents an unreasonably high reading for a single billing period.
SPIKE_THRESHOLD_KWH = Decimal("100000")

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_date(raw: str):
    """Try multiple date formats. Returns a date object or None."""
    if not raw or not raw.strip():
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


def _parse_decimal(raw: str):
    """Return a Decimal or None for invalid/missing values."""
    if not raw or not raw.strip():
        return None
    try:
        return Decimal(raw.strip().replace(",", ""))
    except InvalidOperation:
        return None


# ── Main service function ─────────────────────────────────────────────────────

def normalize_utility_upload(upload_job) -> dict:
    """
    Process all pending RawRecords for the given UTILITY UploadJob.

    Returns a summary dict:
      {
        "records_normalized": int,
        "records_failed": int,
        "validation_issues_created": int,
      }
    """
    organization = upload_job.datasource.organization

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

        # ── Parse usage_kwh ───────────────────────────────────────────────────
        raw_usage = payload.get("usage_kwh", "")
        value = _parse_decimal(raw_usage)

        if value is None:
            errors.append(f"Invalid or missing 'usage_kwh': '{raw_usage}'.")
        elif value < 0:
            errors.append(f"Negative 'usage_kwh' ({value}) is not allowed.")
        elif value > SPIKE_THRESHOLD_KWH:
            warnings.append(
                f"Abnormal spike detected: usage_kwh={value} exceeds threshold "
                f"of {SPIKE_THRESHOLD_KWH} kWh."
            )

        # ── Parse billing dates ───────────────────────────────────────────────
        billing_start = _parse_date(payload.get("billing_start", ""))
        billing_end = _parse_date(payload.get("billing_end", ""))

        if billing_start is None:
            errors.append(
                f"Invalid or missing 'billing_start': '{payload.get('billing_start')}'."
            )
        if billing_end is None:
            errors.append(
                f"Invalid or missing 'billing_end': '{payload.get('billing_end')}'."
            )
        if billing_start and billing_end and billing_end <= billing_start:
            errors.append(
                f"'billing_end' ({billing_end}) must be after 'billing_start' ({billing_start})."
            )

        # ── Hard errors → mark failed ─────────────────────────────────────────
        if errors:
            raw.processing_status = RawRecord.ProcessingStatus.FAILED
            raw.error_message = " | ".join(errors)
            raw.save(update_fields=["processing_status", "error_message"])
            records_failed += 1
            continue

        # ── Use billing_end as the canonical record date ───────────────────────
        record_date = billing_end

        # ── Derive activity label from meter_id ───────────────────────────────
        meter_id = payload.get("meter_id", "unknown_meter").strip()
        tariff = payload.get("tariff", "").strip()
        activity_type = f"Electricity — Meter {meter_id}"
        if tariff:
            activity_type += f" ({tariff})"

        # ── Calculate CO2e ────────────────────────────────────────────────────
        co2e_value = (value * ELECTRICITY_EMISSION_FACTOR).quantize(Decimal("0.000001"))

        # ── Create EmissionRecord ─────────────────────────────────────────────
        emission_record = EmissionRecord.objects.create(
            organization=organization,
            source_type=EmissionRecord.SourceType.UTILITY,
            scope_category=EmissionRecord.ScopeCategory.SCOPE_2,
            activity_type=activity_type,
            value=value,
            unit="kWh",
            normalized_unit="KWH",
            co2e_value=co2e_value,
            emission_factor=ELECTRICITY_EMISSION_FACTOR,
            record_date=record_date,
            approval_status=EmissionRecord.ApprovalStatus.PENDING,
            locked=False,
        )

        # ── Soft warnings → ValidationIssues ──────────────────────────────────
        for msg in warnings:
            validation_issues_to_create.append(
                ValidationIssue(
                    emission_record=emission_record,
                    issue_type="SPIKE_DETECTED",
                    severity=ValidationIssue.Severity.HIGH,
                    message=msg,
                )
            )

        # ── Mark RawRecord normalized ─────────────────────────────────────────
        raw.processing_status = RawRecord.ProcessingStatus.NORMALIZED
        raw.save(update_fields=["processing_status"])
        records_normalized += 1

    # ── Bulk create ValidationIssues ──────────────────────────────────────────
    if validation_issues_to_create:
        ValidationIssue.objects.bulk_create(validation_issues_to_create)

    return {
        "records_normalized": records_normalized,
        "records_failed": records_failed,
        "validation_issues_created": len(validation_issues_to_create),
    }
