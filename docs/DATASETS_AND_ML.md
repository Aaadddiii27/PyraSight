# PyraSight — Datasets and Machine Learning Documentation

## 1. Overview

PyraSight integrates multiple datasets and machine learning models for wildfire-related classification and geospatial awareness.

The project uses three main data sources:

1. Algerian Forest Fires dataset.
2. Mesogeos danger-forecasting dataset.
3. NASA FIRMS VIIRS thermal-detection records.

These sources serve different purposes. Historical datasets are used for model development and evaluation, while FIRMS records provide satellite thermal-detection information for the Global Fire Map.

---

## 2. Dataset Information

### 2.1 Algerian Forest Fires Dataset

**Purpose:** Fire versus no-fire classification.

Dataset characteristics:

| Property | Value |
|---|---:|
| Total records | 1,215 |
| Number of features | 10 |
| Fire records | 633 |
| No-fire records | 582 |

The dataset contains environmental and fire-weather variables.

The features include:

- Temperature
- Relative Humidity (RH)
- Wind Speed (Ws)
- Rain
- Fine Fuel Moisture Code (FFMC)
- Duff Moisture Code (DMC)
- Drought Code (DC)
- Initial Spread Index (ISI)
- Buildup Index (BUI)
- Fire Weather Index (FWI)

The target represents fire or no-fire classification.

**Selected model:** XGBoost.

### 2.2 Mesogeos Danger-Forecasting Dataset

**Purpose:** Fire-danger classification.

The dataset contains positive and negative sample sequences.

| Dataset File | Records |
|---|---:|
| positives.csv | 257,220 |
| negatives.csv | 520,260 |
| Total | 777,480 |

Additional dataset characteristics:

- Positive sample groups: 8,574.
- Negative sample groups: 17,342.
- Each sample group contains 30 rows.
- Coordinates remain consistent within each sample group.
- Data spans approximately April 2006 to September 2022.

The dataset includes environmental and geographical features, along with metadata such as:

- `time`
- `time_idx`
- `sample`
- `x`
- `y`

Metadata and target-related fields are handled separately from the model input features.

The 30-row sample groups are important for preventing related observations from being distributed across different partitions.

### 2.3 NASA FIRMS VIIRS Data

**Purpose:** Geospatial visualization of satellite thermal detections.

The project combines three FIRMS CSV files.

Total loaded detection records:

**1,380,628**

The application currently exposes up to 5,000 records in the Global Fire Map request.

Relevant detection fields include:

- Latitude
- Longitude
- Satellite
- Confidence
- Acquisition date
- Acquisition time
- Fire Radiative Power (FRP)
- Brightness temperature
- Scan
- Track
- Day/Night
- Product

The data is used to display satellite thermal detections on the interactive map.

**Important:** Thermal anomalies detected by satellites are not necessarily confirmed wildfires.

---

## 3. Machine Learning Models

PyraSight maintains three separate model artifact groups.

| Model | Algorithm | Task |
|---|---|---|
| Algerian classifier | XGBoost | Fire / no-fire classification |
| Mesogeos temporal | XGBoost | Fire-danger classification |
| Mesogeos spatial | Random Forest | Fire-danger classification |

The Mesogeos temporal and spatial models use different evaluation protocols and must be interpreted separately.

---

## 4. Algerian Model Training and Evaluation

### Training Configuration

- Dataset: Algerian Forest Fires.
- Total records: 1,215.
- Training records: 973.
- Test records: 242.
- Split: Stratified random train-test split.
- Selected algorithm: XGBoost.
- Model selection: Cross-validation.

### Cross-Validation Results

| Model | Accuracy | F1 Score | ROC-AUC |
|---|---:|---:|---:|
| Logistic Regression | 88.48% | 88.89% | 96.39% |
| Random Forest | 89.63% | 89.65% | 96.86% |
| XGBoost | 89.79% | 89.91% | 96.75% |

### Held-Out Test Results

| Metric | Result |
|---|---:|
| Accuracy | 92.56% |
| Precision | 94.26% |
| Recall | 91.27% |
| F1 Score | 92.74% |
| ROC-AUC | 96.70% |
| PR-AUC | 95.73% |

Confusion matrix:

```text
[[109, 7],
 [ 11, 115]]
```

### SHAP Feature Importance

The most important features in the reported SHAP analysis were:

| Feature | Importance |
|---|---:|
| FWI | 2.3971 |
| FFMC | 1.9109 |
| ISI | 1.1254 |
| Ws | 0.5691 |
| Temperature | 0.4768 |
| DC | 0.3824 |
| DMC | 0.2933 |
| RH | 0.2813 |
| BUI | 0.2544 |
| Rain | 0.1337 |

These values represent global feature importance from the reported SHAP analysis, not causal effects.

---

## 5. Mesogeos Temporal Model

### Evaluation Strategy

A chronological group-aware split was implemented.

The split boundaries were:

| Partition | Time Period |
|---|---|
| Training | Groups fully ending on or before 2018-12-31 |
| Validation | Groups fully contained between 2019-01-01 and 2020-12-31 |
| Test | Groups starting on or after 2021-01-01 |

Groups crossing partition boundaries were excluded.

Negative sample groups were deterministically sampled at up to a 2:1 negative-to-positive group ratio per period.

Training was capped at 199,980 rows using complete 30-row groups.

### Group Counts

| Partition | Positive Groups | Negative Groups |
|---|---:|---:|
| Training | 5,951 | 11,902 |
| Validation | 1,241 | 2,482 |
| Test | 1,367 | 2,717 |

### Model Selection

Validation F1 scores:

| Model | Validation F1 |
|---|---:|
| Logistic Regression | 0.6454 |
| Random Forest | 0.6829 |
| XGBoost | 0.6968 |

**Selected model: XGBoost**

### Held-Out Temporal Test Results

| Metric | Result |
|---|---:|
| Accuracy | 79.51% |
| Precision | 67.37% |
| Recall | 75.21% |
| F1 Score | 71.07% |
| ROC-AUC | 86.84% |
| PR-AUC | 78.38% |

### SHAP Feature Importance

Top reported features:

| Feature | Importance |
|---|---:|
| smi | 0.498744 |
| t2m | 0.442243 |
| slope | 0.437531 |
| ndvi | 0.313544 |
| d2m | 0.288015 |
| population | 0.283295 |
| sp | 0.264860 |
| ssrd | 0.255691 |
| lc_agriculture | 0.183403 |
| curvature | 0.176549 |

---

## 6. Mesogeos Spatial Model

### Evaluation Strategy

The spatial evaluation uses geographic blocks to separate training and held-out locations.

A 25 km buffer was applied between training locations and held-out locations.

Initial split:

| Partition | Groups |
|---|---:|
| Training | 16,274 |
| Validation | 4,729 |
| Test | 4,913 |

After applying the 25 km training buffer:

- 5,017 training groups were removed.
- Remaining training groups: 11,257.

Training was capped to 6,666 complete sample groups:

- Positive groups: 2,220.
- Negative groups: 4,446.
- Training rows: 199,980.

### Model Selection

| Model | Validation F1 | Validation ROC-AUC |
|---|---:|---:|
| Logistic Regression | 0.5843 | 0.7924 |
| Random Forest | 0.6884 | 0.8444 |
| XGBoost | 0.6250 | 0.8404 |

**Selected model: Random Forest**

### Held-Out Spatial Test Results

| Metric | Result |
|---|---:|
| Accuracy | 77.93% |
| Precision | 62.28% |
| Recall | 60.05% |
| F1 Score | 61.15% |
| ROC-AUC | 81.40% |
| PR-AUC | 65.42% |

### SHAP Feature Importance

Top reported features:

| Feature | Importance |
|---|---:|
| smi | 0.073082 |
| t2m | 0.064036 |
| slope | 0.063529 |
| d2m | 0.053866 |
| sp | 0.039651 |
| ssrd | 0.034019 |
| population | 0.025556 |
| lc_shrubland | 0.023871 |
| lst_day | 0.023530 |
| lst_night | 0.023013 |

---

## 7. Model Artifacts

The project stores trained models and supporting artifacts separately.

Expected artifact groups:

```text
artifacts/
│
├── algerian/
│
├── mesogeos/
│   ├── xgboost.pkl
│   ├── imputer.pkl
│   ├── scaler.pkl
│   ├── schema.json
│   └── evaluation.json
│
└── mesogeos_spatial/
    ├── random_forest.pkl
    ├── imputer.pkl
    ├── scaler.pkl
    └── schema.json
```

The exact contents depend on the generated artifacts present in the project.

The temporal model uses its saved imputer during inference to preserve the training preprocessing pipeline.

Pickle artifacts should only be loaded from trusted sources.

---

## 8. Preprocessing and Leakage Considerations

The Mesogeos temporal pipeline uses training-fitted preprocessing.

The median imputer is fitted using training data, and the scaler is fitted using the training partition.

The selected model is subsequently refitted using training and validation data, with preprocessing fitted on those combined partitions, before final test evaluation.

The spatial evaluation uses geographic block splitting and a training buffer to reduce spatial leakage between training and held-out locations.

The Algerian evaluation uses a stratified random split. Its geographic and temporal generalization has not been independently established.

A complete absence of all possible data leakage should not be claimed without additional source-level verification.

---

## 9. Evaluation Limitations

The evaluation protocols have important limitations.

### 9.1 Different Evaluation Protocols

The temporal model is evaluated chronologically, while the spatial model is evaluated geographically.

Their held-out test metrics are not directly comparable.

### 9.2 Spatial Independence

The spatial protocol maintains a minimum training-to-held-out distance of approximately 25 km.

However, the minimum distance between validation and test locations was approximately 1.8176 km.

Therefore, validation and test locations are not fully spatially independent.

### 9.3 Dataset Coverage

The Algerian dataset has limited geographic and temporal coverage.

Mesogeos samples cover a broader period and geographic area, but still have dataset-specific sampling characteristics.

### 9.4 Satellite Detection Interpretation

FIRMS thermal detections are satellite observations and are not necessarily confirmed wildfire incidents.

### 9.5 Operational Forecasting

The current application does not establish operational real-time wildfire forecasting capability.

Model predictions should be interpreted as research outputs based on historical training data and supplied features.

---

## 10. Recommended Reproducibility Practices

For reproducible model development:

1. Preserve original datasets and record their sources.
2. Keep training scripts and generated artifacts together.
3. Record random seeds and split strategies.
4. Keep temporal and spatial evaluation outputs separate.
5. Save preprocessing artifacts alongside trained models.
6. Record model evaluation metrics.
7. Document feature schemas.
8. Avoid modifying test data based on evaluation results.
9. Record software dependencies.
10. Keep dataset limitations visible in project documentation.

---

## 11. Conclusion

PyraSight combines historical wildfire datasets, machine learning classifiers, satellite thermal-detection visualization, and geospatial awareness.

The project evaluates models using both chronological and spatial validation strategies to examine different generalization challenges.

The resulting metrics provide experimental evidence within the evaluated datasets and protocols. They should not be interpreted as proof of operational wildfire prediction performance.

---

**End of Datasets and ML Documentation** 