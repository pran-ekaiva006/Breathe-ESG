# ESG Data Sources Research

This document outlines the real-world considerations, assumptions, and limitations for the data ingestion pipelines.

## 1. SAP (Scope 1 - Direct Emissions)
- **Researched Real-World Format**: SAP exports (via ALV grids or standard BI reporting) are typically flattened tabular data. Standard Material Management (MM) modules output material codes, storage locations (plants), fuel types, and quantities.
- **Why Chosen**: Represents the largest source of Scope 1 emissions for manufacturing and industrial enterprises.
- **Sample Data Assumptions**: We assume standard SI and US Customary units (L, GAL, kg, m3). We assume the `transaction_date` equates directly to the consumption date.
- **Real-World Limitations**: SAP units of measure (UoM) can be highly customized per organization (e.g., "barrels", "BTUs"). Furthermore, transaction dates often reflect accounting posting dates, not physical burning dates.
- **What Would Fail at Enterprise Scale**: Hardcoded unit conversions (`ingestion/normalizer.py`) would fail against custom SAP UoMs. A dynamic, user-configurable unit mapping table would be required for a production enterprise deployment.

## 2. Utility Data (Scope 2 - Indirect Emissions)
- **Researched Real-World Format**: Utility providers provide periodic billing files (often EDI 810 or simple CSVs) detailing meter IDs, service periods, and kWh usage.
- **Why Chosen**: Scope 2 purchased electricity is the most universally applicable ESG metric for any corporate entity with physical offices.
- **Sample Data Assumptions**: We assume non-overlapping `billing_start` and `billing_end` dates, and a clean, positive `usage_kwh` figure.
- **Real-World Limitations**: Real utility bills frequently contain estimated readings, subsequent reversals (true-ups), and overlapping service periods. 
- **What Would Fail at Enterprise Scale**: The current ingestion logic treats every row as a net-new record. At enterprise scale, handling reversals and estimated-to-actual true-ups requires a complex deduplication and event-sourcing engine.

## 3. Business Travel (Scope 3 - Value Chain Emissions)
- **Researched Real-World Format**: Travel management companies (TMCs like Concur or Egencia) export standard reporting files containing passenger names, routing codes (IATA), transport classes, and distances.
- **Why Chosen**: Business travel is the most accessible entry point for Scope 3 emission tracking.
- **Sample Data Assumptions**: We assume distances are accurately pre-calculated by the TMC and that airport codes (JFK, LHR) map cleanly to origin/destination pairs.
- **Real-World Limitations**: Multi-leg flights, class of service (Economy vs. Business impacts emissions differently), and radiative forcing index (RFI) multipliers are highly complex.
- **What Would Fail at Enterprise Scale**: Applying a single, flat emission factor to "distance_km" would fail GHG protocol audits. Real Scope 3 calculation requires dynamically determining short/medium/long-haul flights and applying class-specific emission factors.
