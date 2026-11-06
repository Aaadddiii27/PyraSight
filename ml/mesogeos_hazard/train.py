"""
PyraSight — Mesogeos temporal, group-aware training pipeline.

Split policy:
  Train:      groups fully contained on/before 2018-12-31
  Validation: groups fully contained in 2019-01-01 .. 2020-12-31
  Test:       groups starting on/after 2021-01-01

Each sample is treated as a 30-day group. Groups crossing split boundaries
are excluded so that one sample cannot contribute rows to multiple splits.

This is temporal validation, NOT spatially independent validation:
locations may recur in different periods.
"""

import os
import csv
import json
import pickle
import random
import datetime
import warnings
from collections import defaultdict

warnings.filterwarnings("ignore")

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    classification_report,
)
import xgboost as xgb

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATASET_DIR = os.path.join(
    BASE_DIR, "Dataset", "a.danger_forecasting-20261028T200958Z-1-001",
    "a.danger_forecasting"
)
POSITIVES_PATH = os.path.join(DATASET_DIR, "positives.csv")
NEGATIVES_PATH = os.path.join(DATASET_DIR, "negatives.csv")
NORMS_PATH = os.path.join(DATASET_DIR, "norms.json")
VARS_DICT_PATH = os.path.join(DATASET_DIR, "vars_dict.json")
ARTIFACT_DIR = os.path.join(BASE_DIR, "artifacts", "mesogeos")
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(ARTIFACT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

SEED = 42
TRAIN_END = "2018-12-31"
VAL_START = "2019-01-01"
VAL_END = "2020-12-31"
TEST_START = "2021-01-01"
MAX_TRAIN_ROWS = 200_000
NEGATIVE_TO_POSITIVE_GROUP_RATIO = 2
CHUNK_LOG_EVERY = 100_000

# Exclude identifiers, coordinates, timestamps, and outcome-derived fields.
# x/y/time/sample are retained as metadata only, never as model features.
EXCLUDE_COLS = {
    "time", "time_idx", "sample", "x", "y",
    "ignition_points", "burned_areas", "burned_area_has",
}


def load_feature_info():
    with open(VARS_DICT_PATH, "r", encoding="utf-8") as f:
        vars_dict = json.load(f)
    with open(NORMS_PATH, "r", encoding="utf-8") as f:
        norms = json.load(f)
    print("Static variables:", len(vars_dict.get("static", {})))
    print("Dynamic variables:", len(vars_dict.get("dynamic", {})))
    return vars_dict, norms


def inspect_groups(path, prefix):
    """First pass: discover each 30-day sample's date range and coordinates."""
    groups = {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        required = {"time", "sample", "x", "y"}
        missing = required - set(headers)
        if missing:
            raise ValueError(f"{os.path.basename(path)} missing columns: {sorted(missing)}")

        for row in reader:
            gid = f"{prefix}:{row['sample']}"
            date = row["time"]
            coords = (row["x"], row["y"])
            if gid not in groups:
                groups[gid] = {
                    "start": date, "end": date, "coords": coords, "rows": 0
                }
            g = groups[gid]
            if g["coords"] != coords:
                raise ValueError(f"Inconsistent coordinates in sample group {gid}")
            g["start"] = min(g["start"], date)
            g["end"] = max(g["end"], date)
            g["rows"] += 1

    return groups, headers


def assign_period(group):
    """Assign only wholly-contained groups; discard boundary-crossing groups."""
    start, end = group["start"], group["end"]
    if end <= TRAIN_END:
        return "train"
    if start >= VAL_START and end <= VAL_END:
        return "validation"
    if start >= TEST_START:
        return "test"
    return None


def select_groups(pos_groups, neg_groups):
    """Create deterministic, group-level negative samples for each period."""
    rng = random.Random(SEED)
    selected = {"train": set(), "validation": set(), "test": set()}
    excluded = {"train": 0, "validation": 0, "test": 0}

    for groups in (pos_groups, neg_groups):
        for gid, info in groups.items():
            period = assign_period(info)
            if period is None:
                continue
            selected[period].add(gid)

    # Keep all positive groups; sample negatives at a fixed ratio per period.
    final = {}
    for period in ("train", "validation", "test"):
        positives = sorted(g for g in selected[period] if g.startswith("pos:"))
        negatives = sorted(g for g in selected[period] if g.startswith("neg:"))
        limit = min(
            len(negatives),
            len(positives) * NEGATIVE_TO_POSITIVE_GROUP_RATIO
        )
        rng.shuffle(negatives)
        chosen_negatives = negatives[:limit]
        final[period] = set(positives) | set(chosen_negatives)
        print(
            f"{period.capitalize()} groups: positive={len(positives):,}, "
            f"negative={len(chosen_negatives):,}"
        )
    return final


def load_selected_rows(path, prefix, selected_groups, feature_cols):
    """Second pass: load only rows belonging to selected complete groups."""
    X_parts, y_parts = [], []
    meta = []
    label = 1 if prefix == "pos" else 0
    row_count = 0
    batch = []

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            gid = f"{prefix}:{row['sample']}"
            if gid not in selected_groups:
                continue

            values = []
            for col in feature_cols:
                raw = row.get(col, "")
                try:
                    value = float(raw) if raw is not None and raw.strip() else np.nan
                except (ValueError, AttributeError):
                    value = np.nan
                values.append(value)

            batch.append(values)
            meta.append({
                "sample_group": gid,
                "time": row["time"],
                "x": row["x"],
                "y": row["y"],
            })
            row_count += 1

            if len(batch) >= 25_000:
                X_parts.append(np.asarray(batch, dtype=np.float32))
                batch = []
                if row_count % CHUNK_LOG_EVERY < 25_000:
                    print(f"  Loaded {row_count:,} selected {prefix} rows...")

    if batch:
        X_parts.append(np.asarray(batch, dtype=np.float32))

    if not X_parts:
        return np.empty((0, len(feature_cols)), dtype=np.float32), np.empty(0, dtype=np.int32), meta

    X = np.vstack(X_parts)
    y = np.full(len(X), label, dtype=np.int32)
    return X, y, meta


def load_period_data(period, selected, pos_groups, neg_groups, feature_cols):
    pos_ids = {g for g in selected[period] if g.startswith("pos:")}
    neg_ids = {g for g in selected[period] if g.startswith("neg:")}
    Xp, yp, mp = load_selected_rows(POSITIVES_PATH, "pos", pos_ids, feature_cols)
    Xn, yn, mn = load_selected_rows(NEGATIVES_PATH, "neg", neg_ids, feature_cols)
    X = np.vstack([Xp, Xn])
    y = np.concatenate([yp, yn])
    meta = mp + mn
    return X, y, meta


def metrics(y_true, y_pred, y_prob):
    result = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }
    if len(np.unique(y_true)) == 2:
        result["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        result["pr_auc"] = float(average_precision_score(y_true, y_prob))
    return result


def build_models():
    return {
        "logistic_regression": LogisticRegression(
            max_iter=500, random_state=SEED, C=1.0
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=100, max_depth=12, min_samples_split=10,
            min_samples_leaf=5, random_state=SEED, n_jobs=-1,
            class_weight="balanced"
        ),
        "xgboost": xgb.XGBClassifier(
            n_estimators=150, max_depth=8, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8, random_state=SEED,
            eval_metric="logloss", verbosity=0, n_jobs=-1
        ),
    }


def main():
    print("=== Mesogeos temporal/group-aware training ===")
    print(f"Train end: {TRAIN_END}")
    print(f"Validation: {VAL_START} to {VAL_END}")
    print(f"Test start: {TEST_START}")

    _, _ = load_feature_info()
    pos_groups, pos_headers = inspect_groups(POSITIVES_PATH, "pos")
    neg_groups, neg_headers = inspect_groups(NEGATIVES_PATH, "neg")

    feature_cols = [
        c for c in pos_headers
        if c not in EXCLUDE_COLS and c in neg_headers
    ]
    if not feature_cols:
        raise RuntimeError("No common feature columns found.")

    print(f"\nFeature count: {len(feature_cols)}")
    print("Excluded metadata/outcome fields:", sorted(EXCLUDE_COLS))
    print(
        f"Discovered groups: positive={len(pos_groups):,}, "
        f"negative={len(neg_groups):,}"
    )

    selected = select_groups(pos_groups, neg_groups)

    # Assert no group appears in more than one split.
    sets = [selected["train"], selected["validation"], selected["test"]]
    if sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2]:
        raise RuntimeError("Sample-group leakage detected across splits.")

    data = {}
    for period in ("train", "validation", "test"):
        print(f"\nLoading {period} rows...")
        data[period] = load_period_data(
            period, selected, pos_groups, neg_groups, feature_cols
        )
        X, y, _ = data[period]
        print(
            f"{period}: rows={len(y):,}, fire={int(y.sum()):,}, "
            f"no_fire={int((y == 0).sum()):,}"
        )
        if len(y) == 0 or len(np.unique(y)) < 2:
            raise RuntimeError(
                f"{period} split does not contain both classes. "
                "Review date boundaries or group selection."
            )

    X_train, y_train, _ = data["train"]
    X_val, y_val, _ = data["validation"]
    X_test, y_test, test_meta = data["test"]

    # Bound training size without splitting any 30-row sample group.
    if len(y_train) > MAX_TRAIN_ROWS:
        rng = np.random.default_rng(SEED)
        train_groups = sorted({
            m["sample_group"] for m in data["train"][2]
        })
        # Sample whole groups, preserving both classes and approximate balance.
        pos_ids = [g for g in train_groups if g.startswith("pos:")]
        neg_ids = [g for g in train_groups if g.startswith("neg:")]
        max_groups = MAX_TRAIN_ROWS // 30
        pos_keep = min(len(pos_ids), max_groups // 2)
        neg_keep = min(len(neg_ids), max_groups - pos_keep)
        chosen = set(rng.choice(pos_ids, pos_keep, replace=False).tolist())
        chosen.update(rng.choice(neg_ids, neg_keep, replace=False).tolist())
        keep = np.array([m["sample_group"] in chosen for m in data["train"][2]])
        X_train, y_train = X_train[keep], y_train[keep]
        print(f"Training rows capped at {len(y_train):,} using whole groups.")

    # Fit imputer ONLY on training data. No validation/test statistics leak.
    imputer = SimpleImputer(strategy="median")
    X_train_imp = imputer.fit_transform(X_train)
    X_val_imp = imputer.transform(X_val)
    X_test_imp = imputer.transform(X_test)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_imp)
    X_val_scaled = scaler.transform(X_val_imp)
    X_test_scaled = scaler.transform(X_test_imp)

    models = build_models()
    validation_results = {}
    print("\n=== Validation model selection ===")
    for name, model in models.items():
        Xtr = X_train_scaled if name == "logistic_regression" else X_train_imp
        Xva = X_val_scaled if name == "logistic_regression" else X_val_imp
        model.fit(Xtr, y_train)
        pred = model.predict(Xva)
        prob = model.predict_proba(Xva)[:, 1]
        validation_results[name] = metrics(y_val, pred, prob)
        print(
            f"{name}: F1={validation_results[name]['f1']:.4f}, "
            f"ROC-AUC={validation_results[name].get('roc_auc', float('nan')):.4f}"
        )

    best_name = max(validation_results, key=lambda n: validation_results[n]["f1"])
    print(f"\nSelected on validation F1: {best_name}")

    # Refit chosen model on train + validation, then evaluate test exactly once.
    X_trainval = np.vstack([X_train, X_val])
    y_trainval = np.concatenate([y_train, y_val])
    final_imputer = SimpleImputer(strategy="median")
    X_trainval_imp = final_imputer.fit_transform(X_trainval)
    X_test_final = final_imputer.transform(X_test)

    final_scaler = StandardScaler()
    X_trainval_scaled = final_scaler.fit_transform(X_trainval_imp)
    X_test_scaled_final = final_scaler.transform(X_test_final)

    final_model = build_models()[best_name]
    if best_name == "logistic_regression":
        final_model.fit(X_trainval_scaled, y_trainval)
        test_input = X_test_scaled_final
    else:
        final_model.fit(X_trainval_imp, y_trainval)
        test_input = X_test_final

    test_pred = final_model.predict(test_input)
    test_prob = final_model.predict_proba(test_input)[:, 1]
    test_metrics = metrics(y_test, test_pred, test_prob)

    print("\n=== Held-out temporal test results ===")
    for key in ("accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc"):
        if key in test_metrics:
            print(f"{key}: {test_metrics[key]:.4f}")
    print(classification_report(
        y_test, test_pred, target_names=["no_fire", "fire"], zero_division=0
    ))

    # SHAP on a bounded test sample. Failure is recorded, not silently ignored.
    shap_summary = None
    shap_error = None
    try:
        import shap
        rng = np.random.default_rng(SEED)
        sample_size = min(500, len(test_input))
        idx = rng.choice(len(test_input), sample_size, replace=False)
        X_shap = test_input[idx]
        if best_name in ("random_forest", "xgboost"):
            explainer = shap.TreeExplainer(final_model)
            raw_values = explainer.shap_values(X_shap)
            if isinstance(raw_values, list):
                values = raw_values[1]
            else:
                values = np.asarray(raw_values)
                if values.ndim == 3:
                    values = values[:, :, -1]
            mean_abs = np.abs(values).mean(axis=0)
            shap_summary = {
                feature_cols[i]: float(mean_abs[i])
                for i in range(min(len(feature_cols), len(mean_abs)))
            }
            np.save(os.path.join(ARTIFACT_DIR, "shap_values_sample.npy"), values)
            np.save(os.path.join(ARTIFACT_DIR, "X_shap_sample.npy"), X_shap)
            print("\nSHAP top 10:")
            for feature, importance in sorted(
                shap_summary.items(), key=lambda item: item[1], reverse=True
            )[:10]:
                print(f"  {feature}: {importance:.6f}")
        else:
            shap_error = "SHAP TreeExplainer is configured for tree models only."
    except Exception as exc:
        shap_error = f"{type(exc).__name__}: {exc}"
        print("SHAP generation failed:", shap_error)

    # Save final artifacts only after successful training/evaluation.
    model_path = os.path.join(ARTIFACT_DIR, f"{best_name}.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(final_model, f)
    with open(os.path.join(ARTIFACT_DIR, "imputer.pkl"), "wb") as f:
        pickle.dump(final_imputer, f)
    with open(os.path.join(ARTIFACT_DIR, "scaler.pkl"), "wb") as f:
        pickle.dump(final_scaler, f)

    schema = {
        "feature_columns": feature_cols,
        "meta_columns": ["x", "y", "time", "sample"],
        "target": "binary_fire_danger",
        "target_mapping": {"1": "fire_danger", "0": "no_danger"},
        "model_type": best_name,
        "random_seed": SEED,
        "split_strategy": "chronological_group_aware",
        "train_end": TRAIN_END,
        "validation_start": VAL_START,
        "validation_end": VAL_END,
        "test_start": TEST_START,
        "n_train": int(len(y_train)),
        "n_validation": int(len(y_val)),
        "n_test": int(len(y_test)),
        "geographic_coverage": "Mediterranean region (approximate)",
        "temporal_coverage": "Historical 2006-2022",
        "spatial_independence": False,
    }
    with open(os.path.join(ARTIFACT_DIR, "schema.json"), "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)

    evaluation = {
        "model_name": best_name,
        "validation_results": validation_results,
        "test_results": {best_name: test_metrics},
        "shap_global_importance": shap_summary,
        "shap_error": shap_error,
        "training_timestamp": datetime.datetime.now().isoformat(),
        "dataset": "Mesogeos Danger Forecasting",
        "split_strategy": "chronological_group_aware",
        "date_boundaries": {
            "train_end": TRAIN_END,
            "validation_start": VAL_START,
            "validation_end": VAL_END,
            "test_start": TEST_START,
        },
        "n_train": int(len(y_train)),
        "n_validation": int(len(y_val)),
        "n_test": int(len(y_test)),
        "n_positive_groups": {
            k: sum(g.startswith("pos:") for g in selected[k])
            for k in selected
        },
        "n_negative_groups": {
            k: sum(g.startswith("neg:") for g in selected[k])
            for k in selected
        },
        "limitations": [
            "Temporal split; not spatially independent.",
            "Negative groups are sampled at a fixed ratio to positive groups.",
            "Historical classification results do not establish operational forecast skill.",
        ],
    }
    with open(os.path.join(ARTIFACT_DIR, "evaluation.json"), "w", encoding="utf-8") as f:
        json.dump(evaluation, f, indent=2)

    print("\n[OK] Temporal/group-aware training complete.")
    print("Model:", model_path)
    print("Evaluation:", os.path.join(ARTIFACT_DIR, "evaluation.json"))
    print("IMPORTANT: spatially independent validation is still outstanding.")
    return evaluation


if __name__ == "__main__":
    main()
