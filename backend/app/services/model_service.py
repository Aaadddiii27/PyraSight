"""
PyraSight — Model Service
Loads and serves both ML models for prediction.
"""

import os
import json
import pickle
import logging
import numpy as np
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class AlgerianModel:
    """Wrapper for the Algerian Fire Classifier."""

    def __init__(self, artifact_dir: str):
        self.artifact_dir = artifact_dir
        self.model = None
        self.scaler = None
        self.schema = None
        self.feature_importance = None
        self.loaded = False

    def load(self):
        """Load model artifacts from disk."""
        schema_path = os.path.join(self.artifact_dir, "schema.json")
        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"Algerian schema not found: {schema_path}")

        with open(schema_path) as f:
            self.schema = json.load(f)

        model_type = self.schema.get("model_type", "xgboost")
        model_path = os.path.join(self.artifact_dir, f"{model_type}.pkl")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Algerian model not found: {model_path}")

        with open(model_path, "rb") as f:
            self.model = pickle.load(f)

        scaler_path = os.path.join(self.artifact_dir, "scaler.pkl")
        if os.path.exists(scaler_path):
            with open(scaler_path, "rb") as f:
                self.scaler = pickle.load(f)

        # New temporal Mesogeos artifacts use a train-fitted median imputer.
        # Keep compatibility with older artifacts that do not contain it.
        imputer_path = os.path.join(self.artifact_dir, "imputer.pkl")
        if os.path.exists(imputer_path):
            with open(imputer_path, "rb") as f:
                self.imputer = pickle.load(f)

        fi_path = os.path.join(self.artifact_dir, "feature_importance.json")
        if os.path.exists(fi_path):
            with open(fi_path) as f:
                self.feature_importance = json.load(f)

        eval_path = os.path.join(self.artifact_dir, "evaluation.json")
        if os.path.exists(eval_path):
            with open(eval_path) as f:
                self.evaluation = json.load(f)
        else:
            self.evaluation = {}

        self.loaded = True
        logger.info(f"Algerian model loaded: {model_type}")

    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Make a single prediction from a feature dict."""
        if not self.loaded:
            raise RuntimeError("Model not loaded")

        feature_cols = self.schema["feature_columns"]
        x = np.array([[features.get(col, 0.0) for col in feature_cols]], dtype=np.float32)

        # Apply scaler only for logistic regression
        model_type = self.schema.get("model_type", "xgboost")
        if model_type == "logistic_regression" and self.scaler:
            x_input = self.scaler.transform(x)
        else:
            x_input = x

        pred_class = int(self.model.predict(x_input)[0])
        prob = float(self.model.predict_proba(x_input)[0][1])
        threshold = 0.5

        risk_label = "high" if prob >= 0.7 else "medium" if prob >= 0.4 else "low"

        # Feature contributions (approximate, using feature importances)
        fi = self.feature_importance.get("feature_importance", {}) if self.feature_importance else {}
        contributions = []
        for col in feature_cols:
            val = features.get(col, 0.0)
            imp = fi.get(col, 0.0)
            contributions.append({
                "feature": col,
                "value": val,
                "importance": imp,
                "direction": "increases_fire_risk" if imp > 0 and val > 0 else "decreases_fire_risk"
            })
        contributions.sort(key=lambda x: -x["importance"])

        return {
            "prediction": pred_class,
            "label": "fire" if pred_class == 1 else "not_fire",
            "probability_fire": round(prob, 4),
            "probability_no_fire": round(1 - prob, 4),
            "risk_level": risk_label,
            "threshold": threshold,
            "model_type": model_type,
            "feature_contributions": contributions,
            "disclaimer": (
                "This model classifies current environmental conditions as fire-like or non-fire-like "
                "based on historical Algerian forest fire data. It is NOT a future fire forecast."
            )
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Return model metadata."""
        if not self.loaded:
            return {"status": "not_loaded"}
        return {
            "model_id": "algerian_classifier",
            "model_type": self.schema.get("model_type"),
            "dataset": "Extended Algerian Forest Fires",
            "n_train": self.schema.get("n_train"),
            "n_test": self.schema.get("n_test"),
            "features": self.schema.get("feature_columns"),
            "target": "fire / not_fire",
            "geographic_scope": "Algeria (Bejaia and Sidi Bel-Abbes regions)",
            "status": "ready",
            "evaluation": self.evaluation.get("test_results", {}).get(
                self.schema.get("model_type", "xgboost"), {}
            )
        }


class MesogeoModel:
    """Wrapper for the Mesogeos Wildfire Danger Model."""

    def __init__(self, artifact_dir: str):
        self.artifact_dir = artifact_dir
        self.model = None
        self.scaler = None
        self.imputer = None
        self.schema = None
        self.feature_importance = None
        self.evaluation = {}
        self.loaded = False

    def load(self):
        """Load model artifacts from disk."""
        schema_path = os.path.join(self.artifact_dir, "schema.json")
        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"Mesogeos schema not found: {schema_path}")

        with open(schema_path) as f:
            self.schema = json.load(f)

        model_type = self.schema.get("model_type", "xgboost")
        model_path = os.path.join(self.artifact_dir, f"{model_type}.pkl")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Mesogeos model not found: {model_path}")

        with open(model_path, "rb") as f:
            self.model = pickle.load(f)

        scaler_path = os.path.join(self.artifact_dir, "scaler.pkl")
        if os.path.exists(scaler_path):
            with open(scaler_path, "rb") as f:
                self.scaler = pickle.load(f)

        # The temporal Mesogeos training pipeline fits a median imputer
        # on training data and saves it alongside the model. Load the same
        # fitted transformer so inference uses identical preprocessing.
        imputer_path = os.path.join(self.artifact_dir, "imputer.pkl")
        if os.path.exists(imputer_path):
            with open(imputer_path, "rb") as f:
                self.imputer = pickle.load(f)

        fi_path = os.path.join(self.artifact_dir, "feature_importance.json")
        if os.path.exists(fi_path):
            with open(fi_path) as f:
                self.feature_importance = json.load(f)

        eval_path = os.path.join(self.artifact_dir, "evaluation.json")
        if os.path.exists(eval_path):
            with open(eval_path) as f:
                self.evaluation = json.load(f)

        self.loaded = True
        logger.info(f"Mesogeos model loaded: {model_type}")

    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Make a single prediction from a feature dict."""
        if not self.loaded:
            raise RuntimeError("Model not loaded")

        feature_cols = self.schema["feature_columns"]
        x = np.array([[features.get(col, np.nan) for col in feature_cols]], dtype=np.float32)

        # Apply the exact training-time imputation before optional scaling.
        if self.imputer is not None:
            x = self.imputer.transform(x)

        model_type = self.schema.get("model_type", "xgboost")
        if model_type == "logistic_regression" and self.scaler:
            x_input = self.scaler.transform(x)
        else:
            x_input = x

        pred_class = int(self.model.predict(x_input)[0])
        prob = float(self.model.predict_proba(x_input)[0][1])

        danger_label = "high" if prob >= 0.7 else "moderate" if prob >= 0.4 else "low"

        fi = self.feature_importance.get("feature_importance", {}) if self.feature_importance else {}
        contributions = []
        for col in feature_cols:
            val = features.get(col, 0.0)
            imp = fi.get(col, 0.0)
            contributions.append({
                "feature": col,
                "value": val,
                "importance": imp,
            })
        contributions.sort(key=lambda x: -x["importance"])

        return {
            "prediction": pred_class,
            "label": "fire_danger" if pred_class == 1 else "no_danger",
            "probability_danger": round(prob, 4),
            "probability_safe": round(1 - prob, 4),
            "danger_level": danger_label,
            "model_type": model_type,
            "feature_contributions": contributions[:10],  # top 10
            "disclaimer": (
                "This model was trained on historical Mediterranean fire events. "
                "Predictions reflect patterns in historical data, NOT an operational forecast. "
                "The model distinguishes environmental conditions associated with historical fire events "
                "from conditions that did not precede fires."
            )
        }

    def get_model_info(self) -> Dict[str, Any]:
        if not self.loaded:
            return {"status": "not_loaded"}
        return {
            "model_id": "mesogeos_hazard",
            "model_type": self.schema.get("model_type"),
            "dataset": "Mesogeos Danger Forecasting",
            "n_train": self.schema.get("n_train"),
            "n_test": self.schema.get("n_test"),
            "features": self.schema.get("feature_columns"),
            "target": "fire_danger / no_danger",
            "geographic_scope": "Mediterranean region",
            "status": "ready",
            "evaluation": self.evaluation.get("test_results", {}).get(
                self.schema.get("model_type", "xgboost"), {}
            )
        }


class ModelService:
    """Service that manages all ML models."""

    def __init__(self):
        from app.core.config import settings
        self.algerian = AlgerianModel(settings.ALGERIAN_ARTIFACT_DIR)
        self.mesogeos = MesogeoModel(settings.MESOGEOS_ARTIFACT_DIR)
        self.algerian_ready = False
        self.mesogeos_ready = False

    def load_all_models(self):
        """Load all available models — log errors but don't fail completely."""
        try:
            self.algerian.load()
            self.algerian_ready = True
        except Exception as e:
            logger.warning(f"Algerian model unavailable: {e}")

        try:
            self.mesogeos.load()
            self.mesogeos_ready = True
        except Exception as e:
            logger.warning(f"Mesogeos model unavailable: {e}")

    def get_status(self) -> Dict[str, Any]:
        return {
            "algerian_classifier": "ready" if self.algerian_ready else "unavailable",
            "mesogeos_hazard": "ready" if self.mesogeos_ready else "unavailable",
        }
