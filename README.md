# PyraSight

**Wildfire Intelligence, Explainable Predictions & Geospatial Awareness**

PyraSight is an academic wildfire intelligence and decision-support prototype that combines machine learning, geospatial visualization, satellite thermal detections, incident management, alerts, and reporting in a unified web application.

## 1. Project Overview

Wildfires can cause significant damage to forests, ecosystems, infrastructure, and human communities. Early identification of potential fire danger and access to relevant environmental information can support better awareness and decision-making.

PyraSight brings together historical wildfire datasets, machine learning models, NASA FIRMS VIIRS thermal-detection data, and an interactive dashboard.

The system provides users with a centralized interface to explore fire-related information, generate model-based predictions, manage incidents, and view reports.

> **Important:** PyraSight is an academic and research prototype. Its predictions are based on historical datasets and supplied environmental features. They are not operational wildfire forecasts, official warnings, or a substitute for emergency services or authoritative fire-weather systems. Satellite thermal detections are not necessarily confirmed wildfires.

## 2. Main Features

### Command Center
- Dashboard overview of wildfire-related information.
- Active machine learning model status.
- FIRMS detection statistics.
- Detection activity visualization.

### Hazard Forecast
- Environmental feature-based prediction interface.
- Fire-danger classification.
- Prediction probability and danger-level display.
- Model-based inference using trained ML artifacts.

### Global Fire Map
- Interactive geospatial map using MapLibre GL JS.
- NASA FIRMS VIIRS thermal-detection visualization.
- Satellite and confidence filters.
- Detection markers with confidence-based colors.
- Automatic map zoom to detection locations.
- Individual detection details.

### Incident Explorer
- Incident listing and details.
- Incident status management.
- Analyst notes.
- Bookmark functionality.
- Incident editing and deletion.

### Reports & Alerts
- Report generation and downloads.
- Fire activity and detection summaries.
- Model prediction and incident reports.
- Alert-rule management.

### Data Persistence
- SQLite-based local persistence.
- Storage of application records across backend restarts.
- Persistence of incidents, predictions, alerts, and reports.

### Machine Learning
- Algerian fire classification model.
- Mesogeos chronological model.
- Mesogeos spatial model.
- Model evaluation metrics.
- SHAP-based feature importance and explanations.

## 3. Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite |
| Styling | Tailwind CSS |
| Mapping | MapLibre GL JS |
| Backend | Python, FastAPI |
| API Server | Uvicorn |
| Database | SQLite |
| Machine Learning | Scikit-learn, XGBoost |
| Data Processing | NumPy, Pandas |
| Explainability | SHAP |
| Data Source | NASA FIRMS VIIRS |

## 4. Project Structure

```text
PyraSight/
│
├── artifacts/
│   ├── algerian/
│   ├── mesogeos/
│   └── mesogeos_spatial/
│
├── backend/
│   ├── app/
│   ├── data/
│   ├── requirements.txt
│   └── main.py
│
├── docs/
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── ml/
│
├── scripts/
│
├── Dataset/
│
├── DECISIONS.md
├── PROJECT_LOG.md
├── PROJECT_STATE.json
└── README.md
```

Some folders and generated files may be created locally during installation or execution.

## 5. Prerequisites

Recommended development environment:

- Windows 10/11, macOS, or Linux.
- Python 3.11.
- Node.js 20 LTS or later.
- npm.
- Git (for version control).

The original datasets must be placed separately in the expected project locations. Refer to `docs/DATASETS_AND_ML.md` for dataset details.

## 6. Installation and Setup

### Step 1: Clone or obtain the project

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd PyraSight
```

Alternatively, extract the project ZIP.

### Step 2: Set up the backend

Open a terminal:

```powershell
cd backend

py -3.11 -m venv .venv

.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip

pip install -r requirements.txt
```

### Step 3: Start the backend

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Backend:

http://localhost:8000

API documentation:

http://localhost:8000/api/docs

### Step 4: Set up the frontend

Open another terminal:

```powershell
cd frontend

npm install

npm run build

npm run dev
```

Frontend:

http://localhost:5173

The Vite development configuration proxies API requests to the backend at port 8000.

## 7. Database

PyraSight uses SQLite for local application persistence.

The database is stored at:

```text
backend/data/pyrasight.db
```

Application records are retained across backend restarts.

The local database is runtime data and should not be committed to the public Git repository.

## 8. Machine Learning Models

PyraSight contains three main model artifact groups:

| Model | Purpose |
|---|---|
| Algerian XGBoost | Fire / no-fire classification |
| Mesogeos Temporal XGBoost | Chronological group-aware fire-danger classification |
| Mesogeos Spatial Random Forest | Spatially evaluated fire-danger classification |

The Mesogeos models use separate evaluation protocols.

Their performance metrics should not be treated as directly comparable because their train/test split strategies differ.

SHAP is used to inspect feature importance and support model explainability.

Refer to `docs/DATASETS_AND_ML.md` for evaluation results, dataset details, and limitations.

## 9. Data Sources

The project uses:

- Algerian Forest Fires dataset.
- Mesogeos danger-forecasting dataset.
- NASA FIRMS VIIRS thermal-detection data.

FIRMS thermal detections indicate satellite-observed thermal anomalies and should not automatically be interpreted as confirmed wildfire incidents.

Dataset redistribution and usage terms should be checked before publishing the original data.

## 10. Validation

Frontend production build:

```powershell
cd frontend
npm run build
```

Backend API documentation:

```text
http://localhost:8000/api/docs
```

The project has undergone application workflow, persistence, model inference, and UI regression checks during development.

Automated backend and ML test coverage must be assessed separately; a successful frontend build does not establish complete end-to-end validation.

## 11. Security and Repository Hygiene

Do not commit:

- `.env` files or API keys.
- SQLite database files.
- Python virtual environments.
- `node_modules/`.
- Generated frontend `dist/` folders.
- Runtime logs.
- Private credentials.

Only load trusted machine learning pickle artifacts.

## 12. Project Status

As of November 6, 2026:

- Core frontend and backend workflows implemented.
- SQLite persistence implemented and verified.
- Machine learning artifacts trained and evaluated.
- Temporal and spatial evaluation limitations documented.
- Global Fire Map rendering verified.
- Main UI regression checks completed.
- Documentation and deployment preparation in progress.

Deployment is a separate project phase and should not be considered complete until deployment configuration and deployment testing have been verified.

---

**PyraSight — Wildfire Intelligence, Explainable Predictions & Geospatial Awareness.**