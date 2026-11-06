"""
PyraSight — Final Mesogeos ML Verification Audit
Read-only audit: does not train models or modify existing model artifacts.

Run from project root:
    python ml/mesogeos_hazard/final_ml_audit.py
"""

import json
import math
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree

ROOT = Path(__file__).resolve().parents[2]
DATA = (
    ROOT / "Dataset"
    / "a.danger_forecasting-20261028T200958Z-1-001"
    / "a.danger_forecasting"
)
TEMPORAL = ROOT / "artifacts" / "mesogeos"
SPATIAL = ROOT / "artifacts" / "mesogeos_spatial"

POS = DATA / "positives.csv"
NEG = DATA / "negatives.csv"
SPATIAL_MANIFEST = SPATIAL / "spatial_split_manifest.csv"

EARTH_RADIUS_KM = 6371.0088
BUFFER_KM = 25.0
EXPECTED_GROUP_ROWS = 30

EXCLUDED = {
    "time", "time_idx", "sample", "x", "y",
    "ignition_points", "burned_areas", "burned_area_has",
}

def load_json(path):
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def metric_line(evaluation, model_key=None):
    if not evaluation:
        return None
    results = evaluation.get("test_results", {})
    if model_key and model_key in results:
        m = results[model_key]
    elif results:
        m = next(iter(results.values()))
    else:
        return None
    return {
        key: m.get(key)
        for key in ("accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc")
    }

def main():
    print("=== PyraSight Final ML Verification Audit (READ ONLY) ===")
    issues = []
    checks = {}

    # 1. Dataset/schema and excluded columns
    for p in (POS, NEG):
        if not p.exists():
            raise FileNotFoundError(f"Missing dataset file: {p}")

    pos_cols = pd.read_csv(POS, nrows=0).columns.tolist()
    neg_cols = pd.read_csv(NEG, nrows=0).columns.tolist()
    features = [c for c in pos_cols if c in neg_cols and c not in EXCLUDED]

    checks["dataset_feature_count"] = len(features)
    checks["excluded_metadata_columns_present"] = sorted(
        c for c in EXCLUDED if c in pos_cols or c in neg_cols
    )
    checks["feature_columns"] = features

    suspicious_tokens = (
        "target", "label", "class", "fire_flag", "burned",
        "ignition", "fire_occurrence", "outcome",
    )
    suspicious_features = [
        c for c in features
        if any(token in c.lower() for token in suspicious_tokens)
    ]
    checks["suspicious_feature_names"] = suspicious_features
    if suspicious_features:
        issues.append(
            "Review suspicious feature names manually; name-based screening "
            "cannot prove leakage, but these columns need domain verification."
        )

    # 2. Group integrity in source CSVs
    group_audit = {}
    for label, path in ((1, POS), (0, NEG)):
        df = pd.read_csv(
            path, usecols=["sample", "x", "y", "time"],
            dtype={"sample": str}
        )
        grouped = df.groupby("sample").agg(
            rows=("time", "size"),
            unique_x=("x", "nunique"),
            unique_y=("y", "nunique"),
        )
        bad_size = int((grouped["rows"] != EXPECTED_GROUP_ROWS).sum())
        bad_coords = int(
            ((grouped["unique_x"] != 1) | (grouped["unique_y"] != 1)).sum()
        )
        group_audit["positive" if label else "negative"] = {
            "groups": int(len(grouped)),
            "groups_not_30_rows": bad_size,
            "groups_with_inconsistent_coordinates": bad_coords,
        }
        if bad_size or bad_coords:
            issues.append(f"Group integrity issue in {path.name}.")

    checks["source_group_integrity"] = group_audit

    # 3. Load temporal and spatial evaluation metadata
    temporal_eval = load_json(TEMPORAL / "evaluation.json")
    spatial_eval = load_json(SPATIAL / "evaluation.json")
    temporal_schema = load_json(TEMPORAL / "schema.json")
    spatial_schema = load_json(SPATIAL / "schema.json")

    checks["temporal_evaluation_found"] = temporal_eval is not None
    checks["spatial_evaluation_found"] = spatial_eval is not None
    checks["temporal_metrics"] = metric_line(temporal_eval)
    checks["spatial_metrics"] = metric_line(spatial_eval)

    if not temporal_eval:
        issues.append("Temporal evaluation.json not found.")
    if not spatial_eval:
        issues.append("Spatial evaluation.json not found.")

    # 4. Compare schema features to current CSV feature list
    for name, schema in (("temporal", temporal_schema), ("spatial", spatial_schema)):
        if schema:
            model_features = schema.get("feature_columns", [])
            mismatch = model_features != features
            checks[f"{name}_feature_schema_matches_dataset"] = not mismatch
            if mismatch:
                issues.append(
                    f"{name.capitalize()} model feature schema does not exactly "
                    "match current CSV feature order."
                )

    # 5. Spatial manifest and 25 km buffer verification
    if not SPATIAL_MANIFEST.exists():
        issues.append("Spatial split manifest is missing.")
    else:
        manifest = pd.read_csv(SPATIAL_MANIFEST)
        required = {
            "group_id", "label", "longitude", "latitude", "block", "split"
        }
        missing = sorted(required - set(manifest.columns))
        if missing:
            issues.append(f"Spatial manifest missing columns: {missing}")
        else:
            duplicate_ids = int(manifest["group_id"].duplicated().sum())
            split_counts = {}
            for split in ("train", "validation", "test"):
                subset = manifest[manifest["split"] == split]
                split_counts[split] = {
                    "groups": int(len(subset)),
                    "fire": int((subset["label"] == 1).sum()),
                    "no_fire": int((subset["label"] == 0).sum()),
                }

            checks["spatial_manifest_duplicate_group_ids"] = duplicate_ids
            checks["spatial_manifest_split_counts"] = split_counts

            train = manifest[manifest["split"] == "train"]
            held = manifest[manifest["split"].isin(["validation", "test"])]

            if duplicate_ids:
                issues.append("Duplicate sample groups in spatial manifest.")
            if train.empty or held.empty:
                issues.append("Spatial manifest has an empty train or held-out split.")
            else:
                held_rad = np.radians(
                    held[["latitude", "longitude"]].to_numpy(dtype=float)
                )
                train_rad = np.radians(
                    train[["latitude", "longitude"]].to_numpy(dtype=float)
                )
                tree = BallTree(held_rad, metric="haversine")
                dist, _ = tree.query(train_rad, k=1)
                min_km = float(dist.min() * EARTH_RADIUS_KM)
                checks["spatial_min_train_to_heldout_km"] = round(min_km, 4)
                checks["spatial_buffer_pass"] = min_km >= BUFFER_KM - 1e-4
                if min_km < BUFFER_KM - 1e-4:
                    issues.append("Spatial train-to-held-out buffer is below 25 km.")

                # Report validation-to-test proximity. This is NOT a training
                # leakage check, but it matters for how independent model
                # selection and final test are.
                val = manifest[manifest["split"] == "validation"]
                test = manifest[manifest["split"] == "test"]
                if not val.empty and not test.empty:
                    val_rad = np.radians(
                        val[["latitude", "longitude"]].to_numpy(dtype=float)
                    )
                    test_rad = np.radians(
                        test[["latitude", "longitude"]].to_numpy(dtype=float)
                    )
                    val_tree = BallTree(val_rad, metric="haversine")
                    d, _ = val_tree.query(test_rad, k=1)
                    checks["validation_to_test_min_distance_km"] = round(
                        float(d.min() * EARTH_RADIUS_KM), 4
                    )
                    checks["validation_to_test_within_25km"] = int(
                        (d[:, 0] * EARTH_RADIUS_KM < BUFFER_KM).sum()
                    )
                    checks["validation_test_separation_note"] = (
                        "No buffer was imposed between validation and test; "
                        "model selection on validation may be influenced by "
                        "nearby geography. The training-to-held-out buffer "
                        "does not solve this separate issue."
                    )

    # 6. Artifact loadability (read-only)
    artifact_checks = {}
    for name, folder in (("temporal", TEMPORAL), ("spatial", SPATIAL)):
        paths = {
            "model": folder / (
                (load_json(folder / "schema.json") or {}).get("model_type", "")
                + ".pkl"
            ),
            "imputer": folder / "imputer.pkl",
            "scaler": folder / "scaler.pkl",
        }
        artifact_checks[name] = {}
        for kind, path in paths.items():
            artifact_checks[name][kind + "_exists"] = path.exists()
            if path.exists():
                try:
                    with path.open("rb") as f:
                        pickle.load(f)
                    artifact_checks[name][kind + "_loads"] = True
                except Exception as exc:
                    artifact_checks[name][kind + "_loads"] = False
                    artifact_checks[name][kind + "_error"] = (
                        f"{type(exc).__name__}: {exc}"
                    )
                    issues.append(f"{name} {kind} artifact failed to load.")
    checks["artifact_loadability"] = artifact_checks

    # 7. Deployment recommendation based on current integration contract
    checks["deployment_note"] = (
        "The backend currently uses artifacts/mesogeos (temporal model) "
        "unless model_service.py is explicitly changed. The spatial model "
        "is stored separately and is not automatically active in the app."
    )
    checks["limitations_to_document"] = [
        "Mesogeos dataset covers a historical Mediterranean domain.",
        "Temporal and spatial results are different evaluation protocols.",
        "Spatial split is not chronological; time periods may occur in each split.",
        "The 25 km buffer separates training locations from validation/test locations.",
        "No 25 km buffer was imposed between validation and test blocks.",
        "Historical dataset classification metrics do not establish operational forecast skill.",
        "Dataset negative sampling affects precision, PR-AUC and class prevalence.",
        "A feature-name audit cannot prove absence of semantic/temporal leakage.",
    ]

    report = {
        "audit_timestamp": pd.Timestamp.now().isoformat(),
        "audit_type": "read_only",
        "checks": checks,
        "issues_requiring_attention": issues,
        "status": "REVIEW_REQUIRED" if issues else "PASS_WITH_DOCUMENTED_LIMITATIONS",
    }

    out_json = SPATIAL / "final_ml_audit.json"
    out_md = SPATIAL / "final_ml_audit.md"
    SPATIAL.mkdir(parents=True, exist_ok=True)

    with out_json.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    lines = [
        "# PyraSight Final ML Verification Audit",
        "",
        f"**Status:** {report['status']}",
        f"**Timestamp:** {report['audit_timestamp']}",
        "",
        "## Key results",
        "",
        f"- Dataset common feature count: {checks.get('dataset_feature_count')}",
        f"- Spatial train-to-held-out minimum distance: "
        f"{checks.get('spatial_min_train_to_heldout_km', 'not checked')} km",
        f"- Spatial 25 km buffer: {checks.get('spatial_buffer_pass', 'not checked')}",
        f"- Temporal metrics: `{checks.get('temporal_metrics')}`",
        f"- Spatial metrics: `{checks.get('spatial_metrics')}`",
        "",
        "## Issues requiring attention",
        "",
    ]
    lines += [f"- {item}" for item in issues] if issues else ["- None detected by automated checks."]
    lines += ["", "## Limitations to document", ""]
    lines += [f"- {item}" for item in checks["limitations_to_document"]]
    lines += [
        "",
        "## Interpretation",
        "",
        "This is a read-only automated audit. Passing checks do not prove that "
        "all features are semantically free of leakage; domain review of the "
        "feature definitions and data-generation process is still required.",
        "",
    ]
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print("\n=== AUDIT SUMMARY ===")
    print("Feature count:", checks.get("dataset_feature_count"))
    print("Temporal metrics:", checks.get("temporal_metrics"))
    print("Spatial metrics:", checks.get("spatial_metrics"))
    print("Spatial min train-heldout distance:",
          checks.get("spatial_min_train_to_heldout_km"), "km")
    print("Validation-test minimum distance:",
          checks.get("validation_to_test_min_distance_km"), "km")
    print("Issues:", len(issues))
    for issue in issues:
        print(" -", issue)
    print("\nAudit status:", report["status"])
    print("JSON:", out_json)
    print("Markdown:", out_md)
    print("\nNo models trained. No model artifacts modified.")


if __name__ == "__main__":
    main()
