# PyraSight — API Documentation

## 1. Overview

PyraSight uses FastAPI to expose backend functionality to the React frontend.

The backend handles application requests, machine learning inference, FIRMS detection data, incident management, reporting, alerts, and persistent storage.

### Local Development Configuration

| Property | Value |
|---|---|
| Backend framework | FastAPI |
| Server | Uvicorn |
| Default port | 8000 |
| Local base URL | http://localhost:8000 |
| API documentation | http://localhost:8000/api/docs |

## 2. Starting the Backend

Activate the Python virtual environment and start the application:

```powershell
cd backend

.\.venv\Scripts\Activate.ps1

python -m uvicorn app.main:app --reload --port 8000
```

## 3. Interactive API Documentation

FastAPI provides an interactive Swagger interface.

Open:

http://localhost:8000/api/docs

The interface allows developers to:

- Inspect registered API endpoints.
- View request parameters and schemas.
- Execute supported API requests.
- Inspect response bodies and HTTP status codes.

The Swagger interface is the primary reference for the actual registered routes and schemas.

## 4. API Module Overview

The backend contains API functionality for the following application modules:

| Module | Responsibility |
|---|---|
| Models | Model status and prediction-related operations |
| FIRMS | Satellite thermal-detection records |
| Incidents | Incident listing and management |
| Reports | Report generation and downloads |
| Alerts | Alert-rule management |
| Health / Status | Application status, if registered |

The exact endpoint paths, HTTP methods, request schemas, and response schemas should be confirmed from the running Swagger documentation.

## 5. Model API

The model-related API functionality supports the application's machine learning workflows.

Expected operations include:

- Inspecting available model information.
- Checking model readiness.
- Submitting prediction inputs.
- Receiving prediction results.
- Accessing model-related information where supported.

The application includes three model artifact groups:

1. Algerian XGBoost classifier.
2. Mesogeos temporal XGBoost model.
3. Mesogeos spatial Random Forest model.

Prediction requests must follow the feature schema accepted by the corresponding backend endpoint.

## 6. FIRMS API

The FIRMS functionality provides satellite thermal-detection records to the Global Fire Map.

The frontend requests detection records with parameters such as:

- `limit`
- `satellite`
- `confidence`

An example frontend request configuration is:

```text
limit=5000
```

The frontend converts valid latitude and longitude values into GeoJSON features for map rendering.

Detection information can include:

- Latitude
- Longitude
- Satellite
- Confidence
- Acquisition date
- Acquisition time
- Fire Radiative Power
- Brightness temperature
- Day/Night information

Thermal detections are not necessarily confirmed wildfires.

## 7. Incident API

The incident API supports the Incident Explorer module.

Application operations include:

- Listing incidents.
- Retrieving incident information.
- Updating incident information.
- Managing incident status.
- Managing analyst notes.
- Updating bookmark information.
- Deleting incidents.

The application uses SQLite-backed persistence for incident records.

Use the registered Swagger schemas to identify exact request fields and route paths.

## 8. Reports API

The reports functionality supports generating downloadable reports.

The supported report categories include:

- `fire_activity`
- `detection_summary`
- `model_predictions`
- `incident_summary`

The report service supports CSV output for list-based records and JSON output where applicable.

Reports are managed through the application's backend and persistence layer.

## 9. Alerts API

The alerts functionality supports alert-rule management.

The application provides functionality for:

- Creating alert rules.
- Viewing existing alert rules.
- Managing alert information.
- Retaining alert rules through SQLite persistence.

Consult Swagger for the exact route definitions and request schemas.

## 10. Database and Persistence

The backend uses SQLite for local application data.

Database location:

```text
backend/data/pyrasight.db
```

The persistence layer stores application records such as incidents, predictions, reports, and alert rules.

The database is initialized during application startup.

## 11. Error Handling

API clients should handle standard HTTP responses appropriately.

Common HTTP status categories include:

| Status | Meaning |
|---|---|
| 200 | Successful request |
| 201 | Resource created, where applicable |
| 400 | Invalid request |
| 404 | Requested resource or route not found |
| 422 | Request validation error |
| 500 | Internal server error |

The exact status codes depend on the individual endpoint implementation.

## 12. API Verification

To verify the backend API:

1. Start the backend.
2. Open `http://localhost:8000/api/docs`.
3. Inspect the registered endpoints.
4. Expand an endpoint.
5. Select Try it out.
6. Provide the required parameters or request body.
7. Select Execute.
8. Inspect the response and HTTP status code.

## 13. Development Notes

- The frontend communicates with the backend through HTTP requests.
- The Vite development configuration proxies `/api` requests to the local backend.
- The frontend and backend must both be running for the complete application workflow.
- Model artifacts must be available at their expected locations.
- The SQLite database must be accessible to the backend process.
- Production API URLs, CORS settings, and deployment security configuration must be reviewed before deployment.

## 14. Important Documentation Note

This document describes API modules and capabilities at a functional level.

It intentionally does not invent exact endpoint paths or request schemas. The live FastAPI Swagger interface at `/api/docs` is the authoritative source for the registered routes and their actual definitions.

---

**End of API Documentation**