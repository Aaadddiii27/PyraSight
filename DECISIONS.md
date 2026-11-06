# PyraSight — Architectural Decisions Log

## Decision: Binary Classification Task for Mesogeos
**Date:** 2026-10-30  
**Decision:** Use positives.csv and negatives.csv as two classes for binary wildfire-danger classification.  
**Rationale:** Both files share the identical schema. Positives represent grid cells/days where fire ignition was recorded; negatives represent grid cells/days without fire. This is a supported binary classification task.  
**Limitation:** The model predicts conditions associated with historical fire events, not future fire occurrence. It is NOT an operational forecast.

## Decision: Algerian Dataset — Classification Not Forecasting
**Date:** 2026-10-30  
**Decision:** Build a Fire/No-Fire classifier for current environmental conditions, not a future-fire predictor.  
**Rationale:** The dataset contains environmental measurements taken on fire days vs non-fire days. Features include FWI components. Classification is contemporaneous, not predictive of future ignitions.

## Decision: FIRMS Data — Sample Mode
**Date:** 2026-10-30  
**Decision:** Operate in "sample mode" using the downloaded 7-day FIRMS snapshots.  
**Rationale:** NASA FIRMS API requires an API key. Downloaded data covers ~Oct 21–28, 2026. Application will clearly label this as historical sample data.  
**Future work:** Document how to get API key from https://firms.modaps.eosdis.nasa.gov/api/area/

## Decision: Database — SQLite Fallback
**Date:** 2026-10-30  
**Decision:** Use SQLite as the development database instead of PostgreSQL.  
**Rationale:** PostgreSQL is not configured on the development machine. SQLite provides persistent storage for incidents, alerts, predictions without infrastructure setup.  
**Migration path:** SQLAlchemy ORM models are written to be compatible with PostgreSQL; switching requires only a connection string change.

## Decision: No GPU Training
**Date:** 2026-10-30  
**Decision:** Use CPU-based tree models (scikit-learn Random Forest, XGBoost CPU mode).  
**Rationale:** pandas DLLs blocked by Application Control policy make GPU memory management uncertain. CPU tree models are appropriate for the dataset sizes involved (~1215 Algerian rows, ~777K Mesogeos rows).

## Decision: Pandas Import Limitation
**Date:** 2026-10-30  
**Decision:** Pandas DLLs are blocked by Application Control policy in the sandbox. All Python data processing must run with BypassSandbox=true.  
**Impact:** ML training scripts and data inspection run outside the sandbox.  
**Mitigation:** Scripts are fully written and documented; execution output is captured and logged.

## Decision: Mesogeos Spatial Coordinates
**Date:** 2026-10-30  
**Decision:** Use x (longitude) and y (latitude) columns from Mesogeos CSV for geographic display.  
**Rationale:** Coordinates confirmed present in both positives.csv and negatives.csv (e.g., x=-7.82, y=38.12 — Mediterranean region confirmed).  
**Limitation:** Grid cells are approximately 0.1° resolution. Predictions are historical (reconstructed), not operational forecasts.

## Decision: Frontend Stack Confirmation
**Date:** 2026-10-30  
**Decision:** Use React + TypeScript + Vite + Tailwind CSS + shadcn/ui + MapLibre GL JS + Apache ECharts.  
**Rationale:** Specified in requirements. All packages available via npm.

## Decision: FIRMS Schema Normalization
**Date:** 2026-10-30  
**Decision:** All three FIRMS files (J1, J2, SUOMI) use identical VIIRS C2 schema. Normalize by adding a `product` field derived from filename and let `satellite` field distinguish the sensor.  
**Rationale:** Identical column headers across all three files confirmed during inspection.
