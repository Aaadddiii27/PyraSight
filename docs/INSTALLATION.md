# PyraSight — Installation and Setup Guide

## 1. Introduction

This guide explains how to set up and run PyraSight in a local development environment.

PyraSight consists of:

- React + TypeScript frontend.
- Python FastAPI backend.
- SQLite database.
- Machine learning model artifacts.
- Historical datasets and FIRMS detection records.

## 2. System Requirements

Recommended environment:

| Requirement | Version |
|---|---|
| Operating System | Windows 10/11 |
| Python | 3.11 |
| Node.js | 20 LTS or later |
| npm | Compatible with installed Node.js |
| Git | Latest stable version |
| Browser | Chrome, Edge, or Firefox |

## 3. Project Structure

```text
PyraSight/
│
├── artifacts/
├── backend/
│   ├── app/
│   ├── data/
│   └── requirements.txt
│
├── docs/
├── frontend/
│   ├── src/
│   └── package.json
│
├── ml/
├── scripts/
├── Dataset/
│
├── README.md
├── PROJECT_STATE.json
└── PROJECT_LOG.md
```

## 4. Obtain the Project

Clone the GitHub repository:

```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>

cd PyraSight
```

Alternatively, extract the project archive and open the extracted folder in VS Code.

## 5. Backend Installation

### Step 1: Open the backend directory

```powershell
cd backend
```

### Step 2: Create a Python virtual environment

Ensure Python 3.11 is installed.

```powershell
py -3.11 -m venv .venv
```

### Step 3: Activate the environment

```powershell
.\.venv\Scripts\Activate.ps1
```

The terminal should display:

```text
(.venv)
```

### Step 4: Install dependencies

```powershell
python -m pip install --upgrade pip

pip install -r requirements.txt
```

### Step 5: Start the backend

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

The backend should start on:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/api/docs
```

## 6. Frontend Installation

Open a separate terminal.

### Step 1: Open frontend directory

```powershell
cd frontend
```

### Step 2: Install Node.js dependencies

```powershell
npm install
```

### Step 3: Verify production build

```powershell
npm run build
```

### Step 4: Start development server

```powershell
npm run dev
```

The frontend should be available at:

```text
http://localhost:5173
```

## 7. Running the Complete Application

Two terminals are required during local development.

### Terminal 1 — Backend

```powershell
cd "C:\Aditya Folder\Projects\PyraSight\backend"

.\.venv\Scripts\Activate.ps1

python -m uvicorn app.main:app --reload --port 8000
```

### Terminal 2 — Frontend

```powershell
cd "C:\Aditya Folder\Projects\PyraSight\frontend"

npm run dev
```

Once both servers are running, open:

```text
http://localhost:5173
```

## 8. Machine Learning Artifacts

PyraSight requires its trained model artifacts to be present at the expected project locations.

The artifact groups include:

- Algerian XGBoost model.
- Mesogeos temporal XGBoost model.
- Mesogeos spatial Random Forest model.

Supporting artifacts may include:

- Model pickle files.
- Imputer files.
- Scaler files.
- Feature schemas.
- Evaluation reports.
- Feature-importance information.

Do not rename or move these files without updating the corresponding model-loading configuration.

Only use trusted model pickle artifacts.

## 9. Dataset Setup

The original datasets are not included in the latest project archive.

Place the required datasets in the expected locations used by the training scripts.

The project uses:

1. Algerian Forest Fires dataset.
2. Mesogeos danger-forecasting dataset.
3. NASA FIRMS VIIRS detection CSV files.

Refer to `DATASETS_AND_ML.md` for dataset characteristics and usage.

Dataset downloads and redistribution must comply with the respective source terms.

## 10. SQLite Database

The application uses SQLite.

Expected database location:

```text
backend/data/pyrasight.db
```

The database is initialized by the backend.

For a fresh installation, ensure the backend process has permission to create and write to the required data directory.

Do not commit private or local runtime database files to a public repository.

## 11. Troubleshooting

### Python virtual environment not activating

If PowerShell cannot find the activation script, verify that the virtual environment was created successfully:

```powershell
Test-Path .\.venv\Scripts\Activate.ps1
```

If it returns `False`, create the environment again from the backend directory:

```powershell
py -3.11 -m venv .venv
```

### Wrong Python version

Verify:

```powershell
python --version
```

The expected version is Python 3.11.

### Backend dependencies missing

Ensure the virtual environment is active:

```powershell
python -m pip install -r requirements.txt
```

### Backend not starting

Check:

- Correct working directory.
- Active virtual environment.
- Installed dependencies.
- Model artifact paths.
- Database directory permissions.
- Port 8000 availability.

### Frontend build errors

Run:

```powershell
npm install

npm run build
```

Inspect TypeScript and Vite error messages.

### Frontend cannot communicate with backend

Check:

- Backend is running on port 8000.
- Frontend Vite configuration uses the correct proxy target.
- API routes are registered.
- Browser developer console for request errors.

### Model loading errors

Check:

- Model artifacts exist.
- File names match model-loading configuration.
- Preprocessing artifacts are present.
- Python dependencies are installed.
- Pickle artifacts were created using compatible libraries.

## 12. Development Verification Checklist

After installation, verify:

- [ ] Backend starts successfully.
- [ ] FastAPI documentation opens.
- [ ] Frontend starts successfully.
- [ ] Frontend production build succeeds.
- [ ] Command Center loads.
- [ ] Hazard Forecast inference works.
- [ ] Global Fire Map loads detections.
- [ ] Detection details open when selecting markers.
- [ ] Incident Explorer works.
- [ ] Reports and Alerts work.
- [ ] SQLite persistence works across backend restarts.

## 13. Important Notes

- Local development setup is not equivalent to production deployment.
- The current project uses SQLite for local persistence.
- Production deployment requires appropriate database, security, CORS, environment-variable, and storage configuration.
- Original datasets must be obtained separately.
- Satellite thermal detections are not necessarily confirmed wildfires.
- Model predictions are experimental outputs based on historical data and supplied features.
- PyraSight is not an operational wildfire early-warning system.

---

**End of Installation Guide**