# BreatheESG ESG Data Ingestion Platform

## Project Overview

The BreatheESG ESG Data Ingestion Platform is a full-stack application designed to automate the collection, validation, and review of Environmental, Social, and Governance (ESG) source data. The platform streamlines ESG data ingestion by allowing users to upload raw operational data (such as SAP exports, utility bills, and corporate travel records) via CSV. 

Upon ingestion, the platform executes a normalization workflow that extracts relevant metrics, normalizes varying units of measure into standardized carbon equivalents (CO2e), and flags suspicious data. Processed records are then staged for an analyst review workflow, enabling ESG analysts to review, approve, or reject normalized emissions records prior to final reporting.

## Features

* SAP CSV ingestion
* Utility electricity ingestion
* Travel data ingestion
* Data normalization
* Validation engine
* Audit logging
* Analyst approval workflow
* Multi-tenant support

## Architecture Overview

The system architecture cleanly separates concerns between data ingestion, normalization, and review:
* **Backend Apps:** Organized into distinct Django apps including `core`, `organizations`, `ingestion`, `emissions`, `validation_engine`, and `audits`.
* **Frontend Structure:** Built with React and Vite, utilizing a modular component architecture with dedicated views for uploading data and reviewing pending records.
* **Database Design Approach:** Relational schema emphasizing data integrity, auditability, and clear separation between raw ingestion and normalized outputs.
* **Raw vs Normalized Records:** The ingestion pipeline first stores unmodified uploaded data as `RawRecord` instances. Normalizer functions then process these rows into standardized `EmissionRecord` instances, ensuring zero data loss of the original source files.

## Tech Stack

* **Backend:** Django, Django REST Framework, PostgreSQL
* **Frontend:** React, Vite, Tailwind CSS
* **Deployment:** Render, Vercel
* **Containerization:** Docker

## Project Structure

```text
.
├── backend/
│   ├── core/               # Django settings and main configurations
│   ├── organizations/      # Multi-tenant and user organization models
│   ├── ingestion/          # CSV upload, RawRecord models, and normalization logic
│   ├── emissions/          # Normalized EmissionRecord models and review APIs
│   ├── validation_engine/  # Data validation and anomaly detection
│   ├── audits/             # Immutable audit logging mechanisms
│   ├── manage.py           # Django entry point
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── api/            # API client configurations
│   │   ├── components/     # Reusable UI components
│   │   └── pages/          # Main application views (Uploads, Reviews)
│   ├── package.json        # Node dependencies
│   └── vite.config.js      # Vite configuration
├── sample_data/            # Example CSV files for testing ingestion
├── DECISIONS.md            # Architectural decision records
├── MODEL.md                # Data model documentation
├── SOURCES.md              # Documentation on data sources
└── TRADEOFFS.md            # Technical tradeoffs and considerations
```

## Backend Setup

1. **Virtual Environment Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   ```
2. **Dependency Installation**
   ```bash
   pip install -r requirements.txt
   ```
3. **PostgreSQL Setup**
   Ensure PostgreSQL is installed and running locally. Create a database for the project.
4. **.env Setup**
   Create a `.env` file in the `backend/` directory based on `.env.example` and configure your database credentials.
5. **Migrations**
   ```bash
   python manage.py migrate
   ```
6. **Running Server**
   ```bash
   python manage.py runserver
   ```

## Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

## Docker Setup

To run the application using Docker Compose:

```bash
docker compose up --build
```

## API Endpoints

* **Upload APIs**
  * `POST /api/uploads/sap/`: Ingest SAP CSV data
  * `POST /api/uploads/utility/`: Ingest utility CSV data
  * `POST /api/uploads/travel/`: Ingest travel CSV data
  * `POST /api/uploads/<type>/<id>/normalize/`: Normalize raw uploaded records
* **Emissions APIs**
  * `GET /api/emissions/`: Retrieve paginated and filterable list of normalized emission records
* **Approval APIs**
  * `POST /api/emissions/<id>/approve/`: Lock and approve a specific record
  * `POST /api/emissions/<id>/reject/`: Reject a specific record

## Sample Data

The `sample_data/` directory contains CSV files designed to test the ingestion pipelines:
* `sap_sample.csv`: Example SAP fuel procurement data.
* `utility_sample.csv`: Example utility electricity billing records.
* `travel_sample.csv`: Example corporate travel logs.

## Documentation Files

* **MODEL.md**: Detailed descriptions of the database schema and model relationships.
* **DECISIONS.md**: Log of significant architectural and technical decisions made during development.
* **TRADEOFFS.md**: Discussion of engineering compromises, limitations, and chosen technical paths.
* **SOURCES.md**: Overview of expected data structures and fields for the supported ingestion sources.

## Deployment

* **Backend Deployment on Render:** The Django backend is configured for deployment on Render. Ensure environment variables and the PostgreSQL database are properly attached in the Render dashboard.
* **Frontend Deployment on Vercel:** The React frontend is deployed via Vercel. Link the GitHub repository and configure the build settings to point to the `frontend/` root directory.

## Future Improvements

* **Asynchronous processing:** Implement message brokers (e.g., Celery and Redis) to handle CSV parsing and normalization asynchronously for large datasets.
* **Dynamic mapping:** Introduce a UI-driven mapping engine allowing users to map arbitrary CSV columns to internal schemas without code changes.
* **Caching:** Integrate caching layers (e.g., Redis) for the emissions list endpoints to improve read performance during analyst reviews.
* **Expanded integrations:** Develop direct API integrations with common ERP systems (like SAP or Oracle) to bypass manual CSV uploads.
