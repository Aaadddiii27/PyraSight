"""
PyraSight — SHAP Explanation Generation
Uses XGBoost built-in feature importance as SHAP fallback when SHAP DLLs are unavailable.
Saves feature importance to artifacts for API consumption.
"""

import os
import json
import pickle
import numpy as np

def get_feature_importance(model, feature_cols, method="builtin"):
    """
    Get feature importance from a trained model.
    Returns dict: {feature_name: importance_score}
    """
    importance = {}

    try:
        import shap
        # Try SHAP TreeExplainer first
        if hasattr(model, 'predict_proba'):
            explainer = shap.TreeExplainer(model)
            # Create a small background dataset
            n_features = len(feature_cols)
            bg = np.zeros((10, n_features), dtype=np.float32)
            shap_vals = explainer.shap_values(bg)
            if isinstance(shap_vals, list):
                sv = shap_vals[1]
            else:
                sv = shap_vals
            mean_abs = np.abs(sv).mean(axis=0)
            for i, col in enumerate(feature_cols):
                importance[col] = float(mean_abs[i])
            return importance, "shap"
    except Exception:
        pass

    # Fallback: built-in feature importance
    try:
        if hasattr(model, 'feature_importances_'):
            fi = model.feature_importances_
            for i, col in enumerate(feature_cols):
                importance[col] = float(fi[i]) if i < len(fi) else 0.0
            return importance, "builtin_gini" if hasattr(model, 'estimators_') else "builtin_xgb"
        elif hasattr(model, 'coef_'):
            # Logistic regression
            coef = np.abs(model.coef_[0])
            for i, col in enumerate(feature_cols):
                importance[col] = float(coef[i]) if i < len(coef) else 0.0
            return importance, "logistic_coef"
    except Exception as e:
        print(f"Feature importance extraction failed: {e}")

    return {col: 0.0 for col in feature_cols}, "none"


def generate_shap_for_input(model, input_array, feature_cols, use_shap=False):
    """
    Generate explanation for a single prediction.
    Returns list of {feature, value, contribution} dicts.
    """
    contributions = []

    try:
        if use_shap:
            import shap
            explainer = shap.TreeExplainer(model)
            shap_vals = explainer.shap_values(input_array)
            if isinstance(shap_vals, list):
                sv = shap_vals[1]
            else:
                sv = shap_vals
            sv = sv[0] if len(sv.shape) > 1 else sv
            for i, col in enumerate(feature_cols):
                contributions.append({
                    "feature": col,
                    "value": float(input_array[0, i]) if len(input_array.shape) > 1 else float(input_array[i]),
                    "contribution": float(sv[i]),
                    "direction": "increases_fire_risk" if sv[i] > 0 else "decreases_fire_risk",
                    "method": "shap"
                })
            return contributions
    except Exception:
        pass

    # Fallback: use feature importances as a proxy for contribution direction
    try:
        if hasattr(model, 'feature_importances_'):
            fi = model.feature_importances_
            pred_prob = model.predict_proba(input_array)[0][1]
            baseline = 0.5  # neutral baseline

            for i, col in enumerate(feature_cols):
                val = float(input_array[0, i]) if len(input_array.shape) > 1 else float(input_array[i])
                importance = float(fi[i]) if i < len(fi) else 0.0
                # Estimate direction based on value relative to training range
                contribution = importance * (pred_prob - baseline) * (1.0 if val > 0 else -1.0)
                contributions.append({
                    "feature": col,
                    "value": val,
                    "contribution": contribution,
                    "importance": importance,
                    "direction": "increases_fire_risk" if contribution > 0 else "decreases_fire_risk",
                    "method": "approximate"
                })
    except Exception as e:
        for i, col in enumerate(feature_cols):
            val = float(input_array[0, i]) if len(input_array.shape) > 1 else float(input_array[i])
            contributions.append({"feature": col, "value": val, "contribution": 0.0,
                                 "direction": "unknown", "method": "none"})

    return contributions


if __name__ == "__main__":
    # Generate and save SHAP/feature importance for both models
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    for model_name in ["algerian", "mesogeos"]:
        artifact_dir = os.path.join(base_dir, "artifacts", model_name)
        model_path = None
        schema_path = os.path.join(artifact_dir, "schema.json")

        if not os.path.exists(schema_path):
            print(f"Schema not found for {model_name} — skipping")
            continue

        with open(schema_path) as f:
            schema = json.load(f)

        model_type = schema.get("model_type", "")
        model_file = os.path.join(artifact_dir, f"{model_type}.pkl")
        if not os.path.exists(model_file):
            print(f"Model file not found: {model_file}")
            continue

        with open(model_file, "rb") as f:
            model = pickle.load(f)

        feature_cols = schema.get("feature_columns", [])
        importance, method = get_feature_importance(model, feature_cols)

        # Sort by importance
        sorted_importance = dict(sorted(importance.items(), key=lambda x: -x[1]))

        output = {
            "model": model_name,
            "method": method,
            "feature_importance": sorted_importance
        }
        output_path = os.path.join(artifact_dir, "feature_importance.json")
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)

        print(f"{model_name}: Saved feature importance ({method}) to {output_path}")
        print("Top 5 features:")
        for feat, score in list(sorted_importance.items())[:5]:
            print(f"  {feat}: {score:.4f}")
