# BreatheESG Data Model Architecture

This document outlines the core data modeling and architectural decisions for the BreatheESG platform.

## Organization & Multi-Tenancy
- **Organization Model**: The `Organization` entity represents a tenant (e.g., a corporate client). 
- **Multi-Tenancy Strategy**: We use a logical separation strategy (row-level tenancy) rather than physical database schemas or separate databases. Every core domain model (e.g., `DataSource`, `EmissionRecord`, `UploadJob`) includes a direct foreign key to the `Organization`. This allows for efficient querying and connection pooling while relying on application-level filtering (typically via Django QuerySets and DRF permissions) to enforce tenant isolation.

## Data Ingestion & Lineage
- **UploadJob Design**: The `UploadJob` acts as a correlation ID and audit container for a single batch ingestion event. It tracks metadata (who uploaded, when, source type) and provides a state machine (`PENDING`, `NORMALIZING`, `COMPLETED`, `FAILED`) to monitor asynchronous or long-running parsing tasks.
- **RawRecord Purpose**: ESG data from external systems (SAP, utilities, travel agents) is highly variable and often malformed. The `RawRecord` model stores the exact JSON payload extracted from the source file. It serves as an immutable source of truth, enabling replayability for bug fixes in the normalization logic and providing an audit trail back to the exact bytes provided by the customer.

## Normalization & Validation
- **EmissionRecord Normalization Strategy**: `EmissionRecord` represents the normalized, canonical schema for all ESG activity (Scope 1, 2, 3). The normalizer reads `RawRecord` entries and performs unit conversions, date parsing, and standardization (e.g., converting "liters" or "GAL" to a standardized "L"). Standardized values are multiplied by emission factors to produce a unified `co2e_value`. This decoupling prevents source-system inconsistencies from bleeding into the reporting layer.
- **ValidationIssue Workflow**: During normalization, suspect data (e.g., negative fuel quantities, missing dates) is flagged without necessarily halting the entire ingestion pipeline. `ValidationIssue` records are generated and attached to either the `RawRecord` (for fatal parsing errors) or the resulting `EmissionRecord` (for data warnings). This allows analysts to review and resolve data quality problems asynchronously in the "Reviews" dashboard.

## Audit & Compliance
- **Approval Locking Logic**: To maintain compliance with reporting standards (e.g., GHG Protocol), an `EmissionRecord` cannot be modified after it has been reviewed and approved. Once an analyst approves a record, `locked=True` is set on the model. The Django viewsets enforce a `409 Conflict` if any mutation is attempted on a locked record, ensuring data immutability for final reporting.
- **AuditLog Design**: The `AuditLog` model tracks state transitions and critical actions (e.g., status changes from `PENDING` to `APPROVED` or `REJECTED`) for individual `EmissionRecord`s. It records the actor, timestamp, action performed, and optional change reasons, providing the rigorous traceability required for ESG audits.
