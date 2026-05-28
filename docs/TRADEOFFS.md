# Implementation Tradeoffs

This document outlines three deliberate feature exclusions from the MVP and the engineering rationale behind those decisions.

## 1. No Real SAP API Integration
- **Why Excluded**: Direct integration with SAP ERP (via IDoc, BAPI, or OData) requires extensive network tunneling, highly customized client-specific authentication, and SAP functional consultants.
- **Implementation Complexity**: Extremely high. SAP schemas are heavily customized per enterprise. Building a generic connector is unfeasible for an MVP.
- **Production Implications**: Requires a rigid mapping layer and synchronous uptime between the cloud platform and on-premise ERPs. CSV ingestion shifts the data-extraction burden to the client's IT team, guaranteeing a standardized format.
- **Time Tradeoff**: Saved ~4-6 weeks of reverse-engineering SAP enterprise service buses, allowing focus on the core ESG data models.

## 2. No OCR/PDF Parsing for Utility Bills
- **Why Excluded**: Extracting meter readings and kWh usage from scanned PDFs introduces probabilistic data extraction errors. 
- **Implementation Complexity**: High. Requires implementing ML pipelines (e.g., AWS Textract, Google Document AI) and maintaining bounding-box templates for thousands of utility providers.
- **Production Implications**: ESG audits require 100% deterministic accuracy. OCR artifacts (e.g., mistaking a '5' for an 'S') would pollute the emission database, requiring massive human-in-the-loop validation overhead. Relying on CSV ensures deterministic numeric ingestion.
- **Time Tradeoff**: Saved ~3-5 weeks of training extraction models and building manual correction UIs.

## 3. No Advanced RBAC / Authentication
- **Why Excluded**: Implementing granular Role-Based Access Control (RBAC) with Identity Provider (IdP) SSO integration (SAML/OIDC) is necessary for enterprise adoption but over-engineers the MVP's core value proposition.
- **Implementation Complexity**: Moderate to High. Requires setting up external providers (Auth0/Azure AD) alongside complex Django permission classes.
- **Production Implications**: Security is deferred. While current models support organization-level tenancy, production readiness will mandate strict separation of duties (e.g., a "Data Uploader" cannot be a "Data Approver").
- **Time Tradeoff**: Saved ~2-3 weeks of security configuration, allowing accelerated delivery of the normalization engine and analyst dashboards.
