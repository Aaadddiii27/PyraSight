"""
PyraSight — Algerian Forest Fires Preprocessing & Training Pipeline
Phase 3: Train the Extended Algerian Classifier

Dataset: Extended Algerian Forest Fires (1,215 observations)
Target: Binary classification — fire vs not fire
Features: Temperature, Ws (wind speed), Rain, RH, FFMC, DMC, DC, ISI, BUI, FWI
Note: FWI components are contemporaneous with fire labels. This is classification
      of current environmental conditions, NOT prediction of future fire occurrence.
"""

import os
import sys
import json
import pickle
import csv
import datetime
import warnings
warnings.filterwarnings("ignore")

import openpyxl
import numpy as np

# All these work with BypassSandbox=true
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    classification_report
)
from sklearn.pipeline import Pipeline
import xgboost as xgb

# --- Paths ---
# ml/algerian_classifier/train.py -> project root is 2 levels up
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
DATASET_PATH = os.path.join(BASE_DIR, "Dataset", "The extended Algerian forest fires dataset.xlsx")
ARTIFACT_DIR = os.path.join(BASE_DIR, "artifacts", "algerian")
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(ARTIFACT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

FEATURE_COLUMNS = ["Temperature", "Ws", "Rain", "RH", "FFMC", "DMC", "DC", "ISI", "BUI", "FWI"]
TARGET_COLUMN = "Classes"
RANDOM_SEED = 42


def load_algerian_data():
    """Load and clean the Algerian dataset from xlsx."""
    print("Loading Algerian dataset...")
    wb = openpyxl.load_workbook(DATASET_PATH, read_only=True, data_only=True)
    ws = wb["DONAT_data_set"]
    rows = list(ws.rows)
    wb.close()

    headers = [str(cell.value).strip() if cell.value else "" for cell in rows[0]]
    print(f"Headers: {headers}")

    records = []
    skipped = 0
    for row in rows[1:]:
        vals = [cell.value for cell in row]
        if not any(vals):
            skipped += 1
            continue
        record = {}
        for h, v in zip(headers, vals):
            record[h] = v
        records.append(record)

    print(f"Loaded {len(records)} records (skipped {skipped} empty rows)")

    # Build feature matrix
    X_list = []
    y_list = []
    dates = []
    regions = []
    raw_classes = []

    for rec in records:
        # Clean target
        cls = str(rec.get("Classes", "")).strip().lower()
        if cls == "fire":
            label = 1
        elif cls == "not fire":
            label = 0
        else:
            # Skip rows with unexpected labels
            print(f"  Skipping unexpected class: {repr(cls)}")
            continue

        # Extract features
        try:
            feats = []
            for col in FEATURE_COLUMNS:
                # Find column (strip whitespace)
                val = None
                for h, v in rec.items():
                    if h.strip() == col.strip():
                        val = v
                        break
                if val is None:
                    val = 0.0
                feats.append(float(str(val).strip()) if val != "" and val is not None else 0.0)
            X_list.append(feats)
            y_list.append(label)
            dates.append(rec.get("DATE"))
            raw_classes.append(cls)
            # Region info
            region_col = headers[-1] if len(headers) > 12 else "Unknown"
            regions.append(str(rec.get(region_col, "Unknown")))
        except (ValueError, TypeError) as e:
            print(f"  Skipping row due to conversion error: {e}")
            continue

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int32)

    print(f"Final dataset: {X.shape[0]} samples, {X.shape[1]} features")
    print(f"Class distribution: fire={int(y.sum())}, not_fire={int((y==0).sum())}")
    return X, y, dates, regions


def compute_metrics(y_true, y_pred, y_prob=None):
    """Compute comprehensive evaluation metrics."""
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }
    if y_prob is not None:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
            metrics["pr_auc"] = float(average_precision_score(y_true, y_prob))
        except Exception:
            pass
    cm = confusion_matrix(y_true, y_pred)
    metrics["confusion_matrix"] = cm.tolist()
    return metrics


def train_and_evaluate():
    """Main training and evaluation pipeline."""
    X, y, dates, regions = load_algerian_data()

    # Cross-validation setup. Scaling must happen inside each CV fold to avoid
    # leaking validation-fold statistics into the training fold.
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)

    models = {
        "logistic_regression": LogisticRegression(
            max_iter=1000, random_state=RANDOM_SEED, C=1.0
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=RANDOM_SEED,
            n_jobs=-1
        ),
        "xgboost": xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=RANDOM_SEED,
            eval_metric="logloss",
            verbosity=0
        )
    }

    cv_results = {}

    print("\n=== Cross-Validation Results ===")
    for name, model in models.items():
        cv_model = (
            Pipeline([("scaler", StandardScaler()), ("model", model)])
            if name == "logistic_regression" else model
        )
        scores = cross_validate(
            cv_model, X, y,
            cv=cv,
            scoring=["accuracy", "precision", "recall", "f1", "roc_auc"],
            return_train_score=True,
            n_jobs=-1
        )
        cv_results[name] = {
            k: {"mean": float(np.mean(v)), "std": float(np.std(v))}
            for k, v in scores.items()
        }
        print(f"\n{name}:")
        for metric in ["test_accuracy", "test_f1", "test_roc_auc"]:
            m = cv_results[name][metric]
            print(f"  {metric}: {m['mean']:.4f} ± {m['std']:.4f}")

    # Select best model by F1
    best_name = max(
        cv_results.keys(),
        key=lambda n: cv_results[n]["test_f1"]["mean"]
    )
    print(f"\nBest model: {best_name} (F1={cv_results[best_name]['test_f1']['mean']:.4f})")

    # Final train/test split (80/20 stratified)
    np.random.seed(RANDOM_SEED)
    n = len(X)
    indices = np.arange(n)
    np.random.shuffle(indices)

    # Stratified split
    pos_idx = indices[y[indices] == 1]
    neg_idx = indices[y[indices] == 0]
    n_pos_test = max(1, int(len(pos_idx) * 0.2))
    n_neg_test = max(1, int(len(neg_idx) * 0.2))

    test_idx = np.concatenate([pos_idx[:n_pos_test], neg_idx[:n_neg_test]])
    train_idx = np.concatenate([pos_idx[n_pos_test:], neg_idx[n_neg_test:]])

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    # Fit preprocessing on training data only; never use test statistics.
    scaler = StandardScaler()
    scaler.fit(X_train)

    print(f"\nTrain size: {len(X_train)}, Test size: {len(X_test)}")
    print(f"Train: fire={int(y_train.sum())}, not_fire={int((y_train==0).sum())}")
    print(f"Test:  fire={int(y_test.sum())}, not_fire={int((y_test==0).sum())}")

    # Train final models and evaluate on test set
    final_results = {}

    for name, model in models.items():
        X_tr = scaler.transform(X_train) if name == "logistic_regression" else X_train
        X_te = scaler.transform(X_test) if name == "logistic_regression" else X_test

        model.fit(X_tr, y_train)
        y_pred = model.predict(X_te)
        y_prob = model.predict_proba(X_te)[:, 1] if hasattr(model, "predict_proba") else None
        metrics = compute_metrics(y_test, y_pred, y_prob)
        final_results[name] = metrics
        print(f"\n{name} (test set):")
        for k, v in metrics.items():
            if k != "confusion_matrix":
                print(f"  {k}: {v:.4f}")
        print(f"  confusion_matrix: {metrics['confusion_matrix']}")
        print(classification_report(y_test, y_pred, target_names=["not_fire", "fire"]))

    # Save the best model
    best_model = models[best_name]
    best_X_tr = scaler.transform(X_train) if best_name == "logistic_regression" else X_train
    best_X_te = scaler.transform(X_test) if best_name == "logistic_regression" else X_test
    best_model.fit(best_X_tr, y_train)

    # SHAP explanations
    print("\nGenerating SHAP explanations...")
    shap_available = False
    shap_values_summary = None
    try:
        import shap
        if best_name in ("random_forest", "xgboost"):
            explainer = shap.TreeExplainer(best_model)
            shap_values = explainer.shap_values(best_X_te)
            # For binary classification, shap_values may be list[2] or array
            if isinstance(shap_values, list):
                sv = shap_values[1]  # positive class
            else:
                sv = shap_values
            mean_abs = np.abs(sv).mean(axis=0).tolist()
            shap_values_summary = {
                FEATURE_COLUMNS[i]: float(mean_abs[i])
                for i in range(len(FEATURE_COLUMNS))
            }
            print("SHAP global importance:")
            for feat, imp in sorted(shap_values_summary.items(), key=lambda x: -x[1]):
                print(f"  {feat}: {imp:.4f}")
            shap_available = True
            # Save shap values for sample predictions
            np.save(os.path.join(ARTIFACT_DIR, "shap_values_test.npy"), sv)
            np.save(os.path.join(ARTIFACT_DIR, "X_test.npy"), best_X_te)
            np.save(os.path.join(ARTIFACT_DIR, "y_test.npy"), y_test)
        else:
            print("SHAP TreeExplainer not applicable for logistic regression — skipping")
    except Exception as e:
        print(f"SHAP generation failed: {e}")

    # Save artifacts
    print("\nSaving model artifacts...")

    # Save model
    model_path = os.path.join(ARTIFACT_DIR, f"{best_name}.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(best_model, f)
    print(f"Saved model: {model_path}")

    # Save scaler
    scaler_path = os.path.join(ARTIFACT_DIR, "scaler.pkl")
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    # Save feature schema
    schema = {
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "target_mapping": {"fire": 1, "not fire": 0},
        "model_type": best_name,
        "random_seed": RANDOM_SEED,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
    }
    schema_path = os.path.join(ARTIFACT_DIR, "schema.json")
    with open(schema_path, "w") as f:
        json.dump(schema, f, indent=2)

    # Save evaluation results
    eval_results = {
        "model_name": best_name,
        "cv_results": cv_results,
        "test_results": final_results,
        "shap_global_importance": shap_values_summary,
        "training_timestamp": datetime.datetime.now().isoformat(),
        "dataset": "Extended Algerian Forest Fires",
        "n_total": int(n),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "train_fire_count": int(y_train.sum()),
        "train_notfire_count": int((y_train == 0).sum()),
        "test_fire_count": int(y_test.sum()),
        "test_notfire_count": int((y_test == 0).sum()),
    }
    eval_path = os.path.join(ARTIFACT_DIR, "evaluation.json")
    with open(eval_path, "w") as f:
        json.dump(eval_results, f, indent=2)

    print(f"Saved evaluation: {eval_path}")

    # Test inference on a sample input
    print("\nTesting inference on sample inputs...")
    sample_fire = np.array([[35.0, 25.0, 0.0, 57.0, 91.8, 35.4, 73.2, 11.8, 45.9, 20.5]], dtype=np.float32)
    sample_nofire = np.array([[21.0, 10.0, 3.0, 80.0, 52.0, 4.0, 8.0, 0.5, 3.5, 0.2]], dtype=np.float32)

    for label, sample in [("FIRE", sample_fire), ("NOT_FIRE", sample_nofire)]:
        sample_input = scaler.transform(sample) if best_name == "logistic_regression" else sample
        pred = best_model.predict(sample_input)[0]
        prob = best_model.predict_proba(sample_input)[0][1]
        print(f"  {label} sample -> pred={pred}, prob_fire={prob:.4f}")

    print("\n[OK] Training complete!")
    print(f"  Model: {model_path}")
    print(f"  Schema: {schema_path}")
    print(f"  Evaluation: {eval_path}")
    return eval_results


if __name__ == "__main__":
    results = train_and_evaluate()
    best = results["model_name"]
    print(f"\nFinal best model: {best}")
    test_f1 = results["test_results"][best]["f1"]
    test_auc = results["test_results"][best].get("roc_auc", "N/A")
    print(f"Test F1: {test_f1:.4f}")
    print(f"Test ROC-AUC: {test_auc}")
