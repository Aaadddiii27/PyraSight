# PyraSight — Project Development Log

**Project:** PyraSight — Wildfire Intelligence, Explainable Predictions & Geospatial Awareness

**Last Updated:** November 6, 2026

---

## Phase 1 — Command Center Fixes

**Status: COMPLETED**

### Work Completed
- Fixed Active Models KPI calculation.
- Updated frontend model status matching from `available` to `ready`.
- Corrected Detection Activity chart aggregation.
- Aggregated detection counts by date.
- Limited chart display to the latest seven unique dates.

### Verification
- Active Models KPI correctly displayed two ready models.
- Detection Activity chart displayed unique date labels.

---

## Phase 2 — Core Functionality Testing

**Status: COMPLETED**

### Hazard Forecast
- Tested Mesogeos model inference.
- Verified prediction output, probability, danger level, and model information.

### Incident Explorer
- Tested incident creation and detail view.
- Verified status updates.
- Verified analyst notes.
- Verified bookmark functionality.
- Implemented incident editing and deletion.

### Reports & Alerts
- Tested alert rule creation.
- Fixed report-generation compatibility.
- Added support for frontend report types:
  - Fire Activity
  - Detection Summary
  - Model Predictions
  - Incident Summary
- Verified CSV report download and opening in Excel.

---

## Phase 3 — SQLite Persistence

**Status: COMPLETED**

### Work Completed
- Replaced in-memory application storage with SQLite persistence.
- Configured database storage at:

`backend/data/pyrasight.db`

### Verification
- Created a test incident.
- Restarted the backend.
- Verified incident persistence.
- Verified status, notes, and bookmark persistence.
- Verified prediction history persistence.
- Verified alert rule persistence.
- Verified report persistence.

---

## Phase 4 — Machine Learning Verification

**Status: COMPLETED WITH DOCUMENTED LIMITATIONS**

### Algerian Fire Classification
- Dataset size: 1,215 rows.
- Features: 10.
- Classes: 633 fire and 582 no-fire.
- Selected model: XGBoost.

Held-out test results:

| Metric | Result |
|---|---:|
| Accuracy | 92.56% |
| Precision | 94.26% |
| Recall | 91.27% |
| F1 Score | 92.74% |
| ROC-AUC | 96.70% |
| PR-AUC | 95.73% |

### Mesogeos Temporal Model
- Implemented chronological group-aware splitting.
- Kept complete 30-day sample groups together.
- Used training-fitted preprocessing.
- Selected XGBoost using validation F1.
- Saved model, imputer, scaler, schema, and evaluation artifacts.

Held-out temporal test results:

| Metric | Result |
|---|---:|
| Accuracy | 79.51% |
| Precision | 67.37% |
| Recall | 75.21% |
| F1 Score | 71.07% |
| ROC-AUC | 86.84% |
| PR-AUC | 78.38% |

### Mesogeos Spatial Model
- Implemented spatial block-based splitting.
- Applied a 25 km training buffer against held-out locations.
- Selected Random Forest using validation F1.
- Saved spatial model artifacts separately.

Held-out spatial test results:

| Metric | Result |
|---|---:|
| Accuracy | 77.93% |
| Precision | 62.28% |
| Recall | 60.05% |
| F1 Score | 61.15% |
| ROC-AUC | 81.40% |
| PR-AUC | 65.42% |

### Explainability
- Generated SHAP global feature importance for the evaluated models.
- Documented important environmental features.

### Important Limitations
- Algerian dataset has limited geographic and temporal coverage.
- Mesogeos temporal and spatial test protocols are different.
- Their metrics must not be treated as directly comparable.
- Validation and test locations in the spatial protocol are not fully independent.
- FIRMS thermal detections are not necessarily confirmed wildfire incidents.
- Predictions are not operational wildfire forecasts.

---

## Phase 5 — UI Optimization and Final Testing

**Status: COMPLETED**

### Command Center
- Verified KPI and activity chart fixes.

### Global Fire Map
- Fixed detection-rendering race condition.
- Added reliable map readiness handling.
- Added coordinate validation.
- Added automatic map bounds fitting.
- Verified detection markers.
- Verified confidence-based marker colors.
- Verified marker click interaction.
- Verified Detection Details panel.
- Verified satellite and confidence filters.

### Model Inference
- Fixed Mesogeos model imputer loading.
- Ensured inference uses the training-fitted preprocessing artifact.

### Frontend Cleanup
- Removed unreachable JSX from application routing.
- Improved `.gitignore` exclusions.

### Regression Testing
- Verified Command Center.
- Verified Hazard Forecast.
- Verified Incident Explorer.
- Verified Reports & Alerts.
- Verified Global Fire Map.
- Verified navigation and page refresh.
- Verified frontend production build.

---

## Phase 6 — Deployment and Documentation

**Status: IN PROGRESS**

### Documentation Work
- Audited the project structure.
- Created root README.md.
- Created updated PROJECT_STATE.json.
- Created this development log.

### Remaining Work
- Create backend requirements.txt.
- Document project overview.
- Document architecture and data flow.
- Document datasets and ML evaluation.
- Document API endpoints.
- Document installation and setup.
- Prepare deployment configuration.
- Clean repository for GitHub.
- Verify clean-environment installation.
- Perform final deployment testing.

---

## Development Principles

1. Preserve working application functionality.
2. Avoid unnecessary changes to verified code.
3. Keep temporal and spatial ML evaluation artifacts separate.
4. Document limitations honestly.
5. Verify changes through actual application testing.
6. Keep project state and development logs updated.
7. Do not claim deployment completion before verification.

---

**End of Development Log**