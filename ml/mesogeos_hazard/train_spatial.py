"""
PyraSight — Mesogeos spatially buffered training pipeline.

Spatial split:
- Assign complete 30-day sample groups to 1-degree geographic blocks.
- Shuffle occupied blocks with seed 42.
- 20% blocks -> test; next 15% -> validation; remainder -> train.
- Remove training groups within 25 km of ANY validation or test group.
- Keep each sample group wholly within one split.

Validation selects the model. The final model is fitted on the buffered
training split ONLY (not train+validation), because validation locations
are not guaranteed to be geographically separated from test locations.

Artifacts are saved separately under artifacts/mesogeos_spatial.
The existing temporal model artifacts are not overwritten.
"""

import csv
import json
import pickle
import random
import datetime
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.neighbors import BallTree
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report,
)
import xgboost as xgb

# ---------------------------------------------------------------------
# Paths and configuration
# ---------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parents[1]

DATASET_DIR = (
    BASE_DIR
    / "Dataset"
    / "a.danger_forecasting-20261028T200958Z-1-001"
    / "a.danger_forecasting"
)

POSITIVES_PATH = DATASET_DIR / "positives.csv"
NEGATIVES_PATH = DATASET_DIR / "negatives.csv"

ARTIFACT_DIR = BASE_DIR / "artifacts" / "mesogeos_spatial"
LOG_DIR = BASE_DIR / "logs"

SEED = 42
TEST_BLOCK_FRACTION = 0.20
VALIDATION_BLOCK_FRACTION = 0.15
BUFFER_KM = 25.0
EARTH_RADIUS_KM = 6371.0088
MAX_TRAIN_ROWS = 200_000
GROUP_SIZE = 30
SHAP_SAMPLE_SIZE = 500

EXCLUDE_COLS = {
    "time",
    "time_idx",
    "sample",
    "x",
    "y",
    "ignition_points",
    "burned_areas",
    "burned_area_has",
}


def validate_paths():
    for path in (POSITIVES_PATH, NEGATIVES_PATH):
        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {path}")
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------
# Group metadata and exact split recreation
# ---------------------------------------------------------------------

def load_group_metadata(path: Path, prefix: str, label: int):
    """Read only metadata; each sample must be one consistent 30-row group."""
    df = pd.read_csv(
        path,
        usecols=["sample", "x", "y", "time"],
        dtype={"sample": str},
    )
    df["time"] = pd.to_datetime(df["time"], errors="coerce")

    if df["time"].isna().any():
        raise ValueError(f"Invalid timestamps found in {path.name}")

    grouped = (
        df.groupby("sample", sort=True)
        .agg(
            longitude=("x", "first"),
            latitude=("y", "first"),
            start_date=("time", "min"),
            end_date=("time", "max"),
            rows=("time", "size"),
            unique_x=("x", "nunique"),
            unique_y=("y", "nunique"),
        )
        .reset_index()
    )

    bad_rows = grouped[grouped["rows"] != GROUP_SIZE]
    if not bad_rows.empty:
        raise ValueError(
            f"{path.name}: expected {GROUP_SIZE} rows per group; "
            f"found {len(bad_rows)} invalid groups."
        )

    bad_coords = grouped[
        (grouped["unique_x"] != 1) | (grouped["unique_y"] != 1)
    ]
    if not bad_coords.empty:
        raise ValueError(
            f"{path.name}: inconsistent coordinates in "
            f"{len(bad_coords)} sample groups."
        )

    grouped["group_id"] = prefix + ":" + grouped["sample"].astype(str)
    grouped["label"] = label
    grouped["block_lon"] = np.floor(grouped["longitude"].astype(float)).astype(int)
    grouped["block_lat"] = np.floor(grouped["latitude"].astype(float)).astype(int)
    grouped["block"] = list(zip(grouped["block_lon"], grouped["block_lat"]))

    return grouped[
        [
            "group_id",
            "sample",
            "longitude",
            "latitude",
            "start_date",
            "end_date",
            "rows",
            "label",
            "block",
        ]
    ]


def create_spatial_split(groups: pd.DataFrame):
    """
    Reproduce the simulation's block ordering and deterministic shuffle:
    list(groups['block'].unique()), then random.Random(42).shuffle(...).
    """
    blocks = list(groups["block"].unique())
    rng = random.Random(SEED)
    rng.shuffle(blocks)

    n_test = round(len(blocks) * TEST_BLOCK_FRACTION)
    n_validation = round(len(blocks) * VALIDATION_BLOCK_FRACTION)

    test_blocks = set(blocks[:n_test])
    validation_blocks = set(
        blocks[n_test : n_test + n_validation]
    )
    train_blocks = set(
        blocks[n_test + n_validation :]
    )

    groups = groups.copy()
    groups["split"] = groups["block"].map(
        lambda block: (
            "test"
            if block in test_blocks
            else "validation"
            if block in validation_blocks
            else "train"
        )
    )

    if train_blocks & validation_blocks or train_blocks & test_blocks:
        raise RuntimeError("Geographic block overlap detected.")

    return groups


def apply_training_buffer(groups: pd.DataFrame):
    """Remove only training groups closer than 25 km to held-out locations."""
    train = groups[groups["split"] == "train"].copy()
    held_out = groups[
        groups["split"].isin(["validation", "test"])
    ].copy()

    if train.empty or held_out.empty:
        raise RuntimeError("Train or held-out split is empty.")

    held_coords = np.radians(
        held_out[["latitude", "longitude"]].to_numpy(dtype=float)
    )
    train_coords = np.radians(
        train[["latitude", "longitude"]].to_numpy(dtype=float)
    )

    held_tree = BallTree(held_coords, metric="haversine")
    distances, _ = held_tree.query(train_coords, k=1)
    nearest_km = distances[:, 0] * EARTH_RADIUS_KM

    keep = nearest_km >= BUFFER_KM
    kept_train = train.loc[keep].copy()
    removed_train = train.loc[~keep].copy()

    final_groups = pd.concat(
        [
            kept_train,
            groups[groups["split"] == "validation"],
            groups[groups["split"] == "test"],
        ],
        ignore_index=True,
    )

    # Verify the promised buffer, allowing tiny floating-point tolerance.
    if len(kept_train):
        remaining_coords = np.radians(
            kept_train[["latitude", "longitude"]].to_numpy(dtype=float)
        )
        remaining_distances, _ = held_tree.query(remaining_coords, k=1)
        min_distance_km = (
            float(remaining_distances.min()) * EARTH_RADIUS_KM
        )
        if min_distance_km < BUFFER_KM - 1e-6:
            raise RuntimeError(
                f"Buffer verification failed: minimum distance "
                f"{min_distance_km:.6f} km"
            )
    else:
        min_distance_km = None

    return final_groups, train, kept_train, removed_train, min_distance_km


def print_split_table(title: str, groups: pd.DataFrame):
    print(f"\n{title}")
    print("-" * 72)
    for split_name in ("train", "validation", "test"):
        part = groups[groups["split"] == split_name]
        fire = int((part["label"] == 1).sum())
        no_fire = int((part["label"] == 0).sum())
        print(
            f"{split_name:12s} groups={len(part):7,} | "
            f"fire={fire:7,} | no_fire={no_fire:7,}"
        )
        if fire == 0 or no_fire == 0:
            raise RuntimeError(
                f"{split_name} does not contain both classes."
            )


# ---------------------------------------------------------------------
# Feature loading
# ---------------------------------------------------------------------

def get_feature_columns():
    pos_headers = pd.read_csv(POSITIVES_PATH, nrows=0).columns.tolist()
    neg_headers = pd.read_csv(NEGATIVES_PATH, nrows=0).columns.tolist()
    feature_cols = [
        col
        for col in pos_headers
        if col not in EXCLUDE_COLS and col in neg_headers
    ]
    if not feature_cols:
        raise RuntimeError("No common feature columns found.")
    return feature_cols


def load_selected_rows(path: Path, prefix: str, selected_ids: set, feature_cols):
    """Load complete rows for selected groups, preserving original feature order."""
    X_parts = []
    y_parts = []
    loaded_groups = set()
    batch = []
    label = 1 if prefix == "pos" else 0
    row_count = 0

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            group_id = f"{prefix}:{row['sample']}"
            if group_id not in selected_ids:
                continue

            values = []
            for col in feature_cols:
                raw = row.get(col, "")
                try:
                    value = (
                        float(raw)
                        if raw is not None and raw.strip() != ""
                        else np.nan
                    )
                except (ValueError, AttributeError):
                    value = np.nan
                values.append(value)

            batch.append(values)
            loaded_groups.add(group_id)
            row_count += 1

            if len(batch) >= 25_000:
                X_parts.append(np.asarray(batch, dtype=np.float32))
                y_parts.append(
                    np.full(len(batch), label, dtype=np.int32)
                )
                batch = []
                if row_count % 100_000 < 25_000:
                    print(
                        f"  Loaded {row_count:,} selected "
                        f"{prefix} rows..."
                    )

    if batch:
        X_parts.append(np.asarray(batch, dtype=np.float32))
        y_parts.append(np.full(len(batch), label, dtype=np.int32))

    expected_groups = len(selected_ids)
    if loaded_groups != selected_ids:
        missing = len(selected_ids - loaded_groups)
        raise RuntimeError(
            f"{path.name}: {missing} selected groups had no rows."
        )

    if not X_parts:
        return (
            np.empty((0, len(feature_cols)), dtype=np.float32),
            np.empty(0, dtype=np.int32),
        )

    return np.vstack(X_parts), np.concatenate(y_parts)


def cap_training_groups(train_groups: pd.DataFrame):
    """Cap at 200k rows before loading features, preserving class proportions."""
    max_groups = MAX_TRAIN_ROWS // GROUP_SIZE
    if len(train_groups) <= max_groups:
        return train_groups.copy()

    positives = train_groups[train_groups["label"] == 1]
    negatives = train_groups[train_groups["label"] == 0]
    total = len(train_groups)
    pos_keep = round(max_groups * len(positives) / total)
    neg_keep = max_groups - pos_keep

    rng = np.random.default_rng(SEED)
    pos_ids = rng.choice(positives["group_id"].to_numpy(),
                         size=min(pos_keep, len(positives)), replace=False)
    neg_ids = rng.choice(negatives["group_id"].to_numpy(),
                         size=min(neg_keep, len(negatives)), replace=False)
    chosen = set(pos_ids.tolist()) | set(neg_ids.tolist())
    selected = train_groups[train_groups["group_id"].isin(chosen)].copy()

    print(
        f"Training groups capped before feature loading: {len(selected):,} "
        f"({int((selected['label'] == 1).sum()):,} fire, "
        f"{int((selected['label'] == 0).sum()):,} no_fire)."
    )
    return selected


def load_split_data(split_name, groups, feature_cols):
    part = groups[groups["split"] == split_name]
    pos_ids = set(part.loc[part["label"] == 1, "group_id"])
    neg_ids = set(part.loc[part["label"] == 0, "group_id"])

    print(f"Loading {split_name}: positive groups={len(pos_ids):,}")
    X_pos, y_pos = load_selected_rows(
        POSITIVES_PATH, "pos", pos_ids, feature_cols
    )

    print(f"Loading {split_name}: negative groups={len(neg_ids):,}")
    X_neg, y_neg = load_selected_rows(
        NEGATIVES_PATH, "neg", neg_ids, feature_cols
    )

    X = np.vstack([X_pos, X_neg])
    y = np.concatenate([y_pos, y_neg])

    print(
        f"{split_name}: rows={len(y):,}, "
        f"fire={int(y.sum()):,}, "
        f"no_fire={int((y == 0).sum()):,}"
    )
    return X, y


def build_models():
    return {
        "logistic_regression": LogisticRegression(
            max_iter=500,
            random_state=SEED,
            C=1.0,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=100,
            max_depth=12,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=SEED,
            n_jobs=-1,
            class_weight="balanced",
        ),
        "xgboost": xgb.XGBClassifier(
            n_estimators=150,
            max_depth=8,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=SEED,
            eval_metric="logloss",
            verbosity=0,
            n_jobs=-1,
        ),
    }


def calculate_metrics(y_true, y_pred, y_prob):
    result = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(
            precision_score(y_true, y_pred, zero_division=0)
        ),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }
    if len(np.unique(y_true)) == 2:
        result["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        result["pr_auc"] = float(average_precision_score(y_true, y_prob))
    return result


def calculate_shap(model, X_test, feature_cols):
    try:
        import shap

        rng = np.random.default_rng(SEED)
        sample_size = min(SHAP_SAMPLE_SIZE, len(X_test))
        indices = rng.choice(len(X_test), sample_size, replace=False)
        X_sample = X_test[indices]

        explainer = shap.TreeExplainer(model)
        raw_values = explainer.shap_values(X_sample)

        if isinstance(raw_values, list):
            values = np.asarray(raw_values[1])
        else:
            values = np.asarray(raw_values)
            if values.ndim == 3:
                values = values[:, :, -1]

        mean_abs = np.abs(values).mean(axis=0)
        summary = {
            feature_cols[i]: float(mean_abs[i])
            for i in range(min(len(feature_cols), len(mean_abs)))
        }
        np.save(ARTIFACT_DIR / "shap_values_sample.npy", values)
        np.save(ARTIFACT_DIR / "X_shap_sample.npy", X_sample)
        return summary, None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


# ---------------------------------------------------------------------
# Main training workflow
# ---------------------------------------------------------------------

def main():
    validate_paths()

    print("=== PyraSight Mesogeos SPATIAL training ===")
    print(f"Dataset: {DATASET_DIR}")
    print(f"Block split seed: {SEED}")
    print(f"Test blocks: {TEST_BLOCK_FRACTION:.0%}")
    print(f"Validation blocks: {VALIDATION_BLOCK_FRACTION:.0%}")
    print(f"Training buffer: {BUFFER_KM:.1f} km")
    print(f"Artifacts: {ARTIFACT_DIR}")

    print("\n[1/7] Discovering sample groups...")
    positive = load_group_metadata(POSITIVES_PATH, "pos", 1)
    negative = load_group_metadata(NEGATIVES_PATH, "neg", 0)
    groups = pd.concat([positive, negative], ignore_index=True)

    print(
        f"Groups discovered: positive={len(positive):,}, "
        f"negative={len(negative):,}, total={len(groups):,}"
    )

    print("\n[2/7] Creating spatial block split...")
    groups = create_spatial_split(groups)
    print_split_table("INITIAL SPATIAL SPLIT", groups)

    print("\n[3/7] Applying 25 km training buffer...")
    final_groups, original_train, kept_train, removed_train, min_distance = (
        apply_training_buffer(groups)
    )

    print(f"Original train groups: {len(original_train):,}")
    print(f"Removed within buffer: {len(removed_train):,}")
    print(f"Remaining train groups: {len(kept_train):,}")
    print(
        f"Training groups removed: "
        f"{len(removed_train) / max(1, len(original_train)) * 100:.2f}%"
    )
    print(
        "Minimum remaining train-to-held-out distance: "
        f"{min_distance:.2f} km"
        if min_distance is not None
        else "No remaining training groups."
    )
    print_split_table("FINAL SPATIAL SPLIT AFTER BUFFER", final_groups)

    # Cap training at complete groups BEFORE loading feature rows.
    original_train_group_count = int((final_groups["split"] == "train").sum())
    selected_train_groups = cap_training_groups(
        final_groups[final_groups["split"] == "train"]
    )
    final_groups = pd.concat(
        [
            selected_train_groups,
            final_groups[final_groups["split"] == "validation"],
            final_groups[final_groups["split"] == "test"],
        ],
        ignore_index=True,
    )

    # Save exact final split manifest for reproducibility/audit.
    manifest_path = ARTIFACT_DIR / "spatial_split_manifest.csv"
    final_groups[
        ["group_id", "label", "longitude", "latitude", "block", "split"]
    ].to_csv(manifest_path, index=False)

    print("\n[4/7] Loading features...")
    feature_cols = get_feature_columns()
    print(f"Feature count: {len(feature_cols)}")
    print("Excluded metadata/outcome fields:", sorted(EXCLUDE_COLS))

    train_groups = final_groups[final_groups["split"] == "train"].copy()
    X_train, y_train = load_split_data(
        "train", final_groups, feature_cols
    )
    X_val, y_val = load_split_data(
        "validation", final_groups, feature_cols
    )
    X_test, y_test = load_split_data(
        "test", final_groups, feature_cols
    )

    if len(np.unique(y_train)) < 2 or len(np.unique(y_val)) < 2:
        raise RuntimeError("Train and validation must both contain both classes.")
    if len(np.unique(y_test)) < 2:
        raise RuntimeError("Test must contain both classes.")

    print("\n[5/7] Fitting preprocessing on training data only...")
    imputer = SimpleImputer(strategy="median")
    X_train_imp = imputer.fit_transform(X_train)
    X_val_imp = imputer.transform(X_val)
    X_test_imp = imputer.transform(X_test)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_imp)
    X_val_scaled = scaler.transform(X_val_imp)
    X_test_scaled = scaler.transform(X_test_imp)

    print("\n[6/7] Validation model selection...")
    validation_results = {}
    fitted_models = {}

    for name, model in build_models().items():
        Xtr = X_train_scaled if name == "logistic_regression" else X_train_imp
        Xva = X_val_scaled if name == "logistic_regression" else X_val_imp

        model.fit(Xtr, y_train)
        pred = model.predict(Xva)
        prob = model.predict_proba(Xva)[:, 1]

        validation_results[name] = calculate_metrics(y_val, pred, prob)
        fitted_models[name] = model

        print(
            f"{name}: F1={validation_results[name]['f1']:.4f}, "
            f"ROC-AUC={validation_results[name].get('roc_auc', float('nan')):.4f}, "
            f"PR-AUC={validation_results[name].get('pr_auc', float('nan')):.4f}"
        )

    best_name = max(
        validation_results,
        key=lambda name: validation_results[name]["f1"],
    )
    final_model = fitted_models[best_name]
    print(f"\nSelected model by validation F1: {best_name}")

    # IMPORTANT: do not refit on validation. Validation may be spatially
    # close to test. Keep the model trained on buffered train groups only.
    test_input = (
        X_test_scaled if best_name == "logistic_regression" else X_test_imp
    )
    test_pred = final_model.predict(test_input)
    test_prob = final_model.predict_proba(test_input)[:, 1]
    test_metrics = calculate_metrics(y_test, test_pred, test_prob)

    print("\n=== HELD-OUT SPATIAL TEST RESULTS ===")
    for key in (
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "pr_auc",
    ):
        if key in test_metrics:
            print(f"{key}: {test_metrics[key]:.4f}")

    report = classification_report(
        y_test,
        test_pred,
        labels=[0, 1],
        target_names=["no_fire", "fire"],
        zero_division=0,
        output_dict=True,
    )
    print("\nClassification report:")
    print(
        classification_report(
            y_test,
            test_pred,
            labels=[0, 1],
            target_names=["no_fire", "fire"],
            zero_division=0,
        )
    )

    print("\n[7/7] SHAP analysis and saving spatial artifacts...")
    shap_summary = None
    shap_error = None
    if best_name in ("random_forest", "xgboost"):
        shap_summary, shap_error = calculate_shap(
            final_model, test_input, feature_cols
        )
    else:
        shap_error = "Tree SHAP is configured only for tree-based models."

    if shap_summary:
        print("SHAP top 10:")
        for feature, importance in sorted(
            shap_summary.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:10]:
            print(f"  {feature}: {importance:.6f}")
    elif shap_error:
        print("SHAP unavailable:", shap_error)

    model_path = ARTIFACT_DIR / f"{best_name}.pkl"
    with model_path.open("wb") as handle:
        pickle.dump(final_model, handle)

    with (ARTIFACT_DIR / "imputer.pkl").open("wb") as handle:
        pickle.dump(imputer, handle)

    with (ARTIFACT_DIR / "scaler.pkl").open("wb") as handle:
        pickle.dump(scaler, handle)

    schema = {
        "feature_columns": feature_cols,
        "meta_columns": ["x", "y", "time", "sample"],
        "target": "binary_fire_danger",
        "target_mapping": {"1": "fire_danger", "0": "no_danger"},
        "model_type": best_name,
        "random_seed": SEED,
        "split_strategy": "spatial_1_degree_blocks_with_25km_train_buffer",
        "block_assignment": {
            "test_fraction": TEST_BLOCK_FRACTION,
            "validation_fraction": VALIDATION_BLOCK_FRACTION,
            "seed": SEED,
        },
        "buffer_km": BUFFER_KM,
        "minimum_train_to_held_out_distance_km": min_distance,
        "training_refit_policy": "train_only; validation not merged into final fit",
        "n_train": int(len(y_train)),
        "n_validation": int(len(y_val)),
        "n_test": int(len(y_test)),
        "geographic_coverage": "Mediterranean region (approximate)",
        "temporal_coverage": "Historical 2006-2022; spatial split is not chronological",
        "spatial_independence": True,
    }

    evaluation = {
        "model_name": best_name,
        "validation_results": validation_results,
        "test_results": {best_name: test_metrics},
        "classification_report": report,
        "shap_global_importance": shap_summary,
        "shap_error": shap_error,
        "training_timestamp": datetime.datetime.now().isoformat(),
        "dataset": "Mesogeos Danger Forecasting",
        "split_strategy": "spatial_1_degree_blocks_with_25km_train_buffer",
        "buffer_km": BUFFER_KM,
        "minimum_train_to_held_out_distance_km": min_distance,
        "original_buffered_train_groups_before_cap": original_train_group_count,
        "n_groups": {
            split: int((final_groups["split"] == split).sum())
            for split in ("train", "validation", "test")
        },
        "n_fire_groups": {
            split: int(
                (
                    (final_groups["split"] == split)
                    & (final_groups["label"] == 1)
                ).sum()
            )
            for split in ("train", "validation", "test")
        },
        "n_no_fire_groups": {
            split: int(
                (
                    (final_groups["split"] == split)
                    & (final_groups["label"] == 0)
                ).sum()
            )
            for split in ("train", "validation", "test")
        },
        "n_rows": {
            "train": int(len(y_train)),
            "validation": int(len(y_val)),
            "test": int(len(y_test)),
        },
        "limitations": [
            "Spatial holdout is within the dataset geographic domain, not proof of global generalization.",
            "The 25 km buffer is applied from all validation and test sample locations to training locations.",
            "Validation is used for model selection and is not merged into final training.",
            "Negative sample groups are used as provided by the dataset; metrics depend on dataset sampling.",
            "Historical classification performance does not establish operational forecast skill.",
            "The split is spatial, not chronological; time periods may occur in every split.",
        ],
    }

    with (ARTIFACT_DIR / "schema.json").open("w", encoding="utf-8") as handle:
        json.dump(schema, handle, indent=2)

    with (ARTIFACT_DIR / "evaluation.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(evaluation, handle, indent=2)

    print("\n[OK] Spatial training and evaluation complete.")
    print("Model:", model_path)
    print("Artifacts:", ARTIFACT_DIR)
    print("Evaluation:", ARTIFACT_DIR / "evaluation.json")
    print("Split manifest:", manifest_path)
    print("Temporal artifacts were not modified.")

    return evaluation


if __name__ == "__main__":
    main()
