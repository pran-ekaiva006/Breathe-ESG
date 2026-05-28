"""
Travel Normalization Service
=============================
Reads pending RawRecord rows from a TRAVEL UploadJob and normalizes
them into EmissionRecord rows (Scope 3 — business travel).

Creates ValidationIssue records for:
  - impossible distances (> 20,000 km or <= 0)
  - missing airport codes
  - missing trip dates
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from emissions.models import EmissionRecord
from validation_engine.models import ValidationIssue

from .models import RawRecord

# ── Constants ─────────────────────────────────────────────────────────────────

# ICAO/IATA emission factors (kgCO2e per passenger-km)
TRANSPORT_EMISSION_FACTORS = {
    "air":        Decimal("0.1550"),   # average short + long haul
    "flight":     Decimal("0.1550"),
    "airplane":   Decimal("0.1550"),
    "plane":      Decimal("0.1550"),
    "train":      Decimal("0.0410"),
    "rail":       Decimal("0.0410"),
    "car":        Decimal("0.1710"),
    "taxi":       Decimal("0.2090"),
    "bus":        Decimal("0.0890"),
    "ferry":      Decimal("0.1120"),
}
DEFAULT_EMISSION_FACTOR = Decimal("0.1550")   # fallback = air travel

# Earth's maximum great-circle distance (antipodal points)
MAX_DISTANCE_KM = Decimal("20015")
MIN_DISTANCE_KM = Decimal("0")

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_date(raw: str):
    if not raw or not raw.strip():
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


def _parse_decimal(raw: str):
    if not raw or not raw.strip():
        return None
    try:
        return Decimal(raw.strip().replace(",", ""))
    except InvalidOperation:
        return None


def _get_emission_factor(transport_type: str) -> tuple[Decimal, bool]:
    """Return (factor, is_known). is_known=False means unknown transport."""
    key = transport_type.strip().lower()
    factor = TRANSPORT_EMISSION_FACTORS.get(key)
    return (factor or DEFAULT_EMISSION_FACTOR, factor is not None)


# ── Main service function ─────────────────────────────────────────────────────

def normalize_travel_upload(upload_job) -> dict:
    """
    Process all pending RawRecords for the given TRAVEL UploadJob.

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

        # ── Map: distance_km → value ──────────────────────────────────────────
        raw_distance = payload.get("distance_km", "")
        distance = _parse_decimal(raw_distance)

        if distance is None:
            errors.append(f"Invalid or missing 'distance_km': '{raw_distance}'.")
        elif distance <= MIN_DISTANCE_KM:
            errors.append(f"'distance_km' must be positive (got {distance}).")
        elif distance > MAX_DISTANCE_KM:
            errors.append(
                f"Impossible distance: {distance} km exceeds Earth's max "
                f"great-circle distance ({MAX_DISTANCE_KM} km)."
            )

        # ── Map: transport_type → activity_type ───────────────────────────────
        transport_type = payload.get("transport_type", "").strip()
        if not transport_type:
            errors.append("Missing 'transport_type'.")

        # ── Validate airport codes ────────────────────────────────────────────
        departure = payload.get("departure_airport", "").strip()
        arrival   = payload.get("arrival_airport", "").strip()

        if not departure:
            errors.append("Missing 'departure_airport'.")
        if not arrival:
            errors.append("Missing 'arrival_airport'.")

        # ── Validate trip_date ────────────────────────────────────────────────
        raw_date = payload.get("trip_date", "")
        trip_date = _parse_date(raw_date)
        if trip_date is None:
            errors.append(f"Invalid or missing 'trip_date': '{raw_date}'.")

        # ── Hard errors → mark failed ─────────────────────────────────────────
        if errors:
            raw.processing_status = RawRecord.ProcessingStatus.FAILED
            raw.error_message = " | ".join(errors)
            raw.save(update_fields=["processing_status", "error_message"])
            records_failed += 1
            continue

        # ── Derive emission factor from transport type ─────────────────────────
        emission_factor, type_known = _get_emission_factor(transport_type)

        if not type_known:
            warnings.append(
                f"Unknown transport_type '{transport_type}'. "
                f"Defaulted to air travel factor ({DEFAULT_EMISSION_FACTOR} kgCO2e/km)."
            )

        # ── Build activity label ──────────────────────────────────────────────
        traveler = payload.get("traveler_name", "").strip()
        activity_type = f"{transport_type.title()} — {departure} → {arrival}"
        if traveler:
            activity_type += f" ({traveler})"

        # ── Calculate CO2e ────────────────────────────────────────────────────
        co2e_value = (distance * emission_factor).quantize(Decimal("0.000001"))

        # ── Create EmissionRecord ─────────────────────────────────────────────
        emission_record = EmissionRecord.objects.create(
            organization=organization,
            source_type=EmissionRecord.SourceType.TRAVEL,
            scope_category=EmissionRecord.ScopeCategory.SCOPE_3,
            activity_type=activity_type,
            value=distance,
            unit="km",
            normalized_unit="KM",
            co2e_value=co2e_value,
            emission_factor=emission_factor,
            record_date=trip_date,
            approval_status=EmissionRecord.ApprovalStatus.PENDING,
            locked=False,
        )

        # ── Soft warnings → LOW ValidationIssues ──────────────────────────────
        for msg in warnings:
            validation_issues_to_create.append(
                ValidationIssue(
                    emission_record=emission_record,
                    issue_type="UNKNOWN_TRANSPORT_TYPE",
                    severity=ValidationIssue.Severity.LOW,
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
