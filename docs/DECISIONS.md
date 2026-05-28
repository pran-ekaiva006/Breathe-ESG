# Engineering Decisions and Assumptions

## Core Technology Choices

- **Django REST Framework (DRF)**: Selected because ESG platforms are heavily CRUD-based but require rigorous data validation and complex authorization patterns (row-level, organization-level). DRF's built-in serializers and viewsets handle this boilerplate efficiently. The ORM's ability to model complex hierarchical schemas is crucial for emissions categorization.
- **CSV Ingestion**: Selected over direct API integrations because enterprise source systems (like legacy SAP deployments or localized utility providers) rarely expose modern, uniform REST APIs. CSV exports are the lowest common denominator and the most reliable data extraction method across disjointed corporate IT ecosystems.
- **PostgreSQL**: Chosen for its robust transactional guarantees (ACID) and JSONB support. ESG audit trails require strict transactional consistency, while the `RawRecord` model relies on JSONB to store unpredictable, semi-structured payloads from diverse CSV inputs.

## Data Source Assumptions

- **SAP Exports**: We assumed SAP exports are flat, tabular records where fuel types and physical quantities are mapped cleanly per plant code. We assume the transaction date represents the actual date of fuel consumption, not just an accounting posting date.
- **Utility Systems**: We assumed utility providers export bills covering clear chronological cycles (`billing_start` to `billing_end`) with total `usage_kwh`. We assume there are no overlapping billing periods for the same meter, and that tariff rates are provided directly rather than requiring external lookups.
- **Travel Systems**: We assumed travel agency records provide standard IATA airport codes for flights and that distances are accurately calculated by the agency rather than requiring us to implement a geospatial Haversine formula engine.

## Intentional Simplifications

- **Emission Factors**: Currently simplified to a single constant (`0.233`). In a production system, this would require a complex temporal and regional database (e.g., DEFRA, EPA eGRID) because grid carbon intensity changes yearly and by geographic region.
- **File Parsing**: We currently parse the CSVs semi-synchronously within the HTTP request cycle. For larger enterprise files (millions of rows), this process must be moved to an asynchronous worker queue like Celery to prevent API timeouts.
- **Role-Based Access Control (RBAC)**: Simplified. True multi-tenancy would require granular RBAC (e.g., Data Entry vs. Auditor vs. Admin) to enforce strict segregation of duties.

## Areas Requiring PM Clarification

- **Missing Data Workflows**: How should the platform behave if a utility bill is missing for a month? Should we interpolate data or halt reporting?
- **Data Remediation**: If an analyst rejects a record due to a bad SAP export, should the system allow them to edit the payload directly in the UI, or force the customer to upload a corrected CSV?
