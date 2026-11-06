"""PyraSight Backend Configuration"""

import os
from typing import List


class Settings:
    """Application settings loaded from environment variables."""

    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "PyraSight"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./pyrasight.db"
    )

    # Paths — go from backend/app/core/config.py up to project root (4 levels)
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    ARTIFACT_DIR: str = os.path.join(BASE_DIR, "artifacts")
    DATASET_DIR: str = os.path.join(BASE_DIR, "Dataset")
    LOG_DIR: str = os.path.join(BASE_DIR, "logs")
    DATABASE_PATH: str = os.path.join(BASE_DIR, "backend", "data", "pyrasight.db")

    # FIRMS data paths
    FIRMS_J1_PATH: str = os.path.join(DATASET_DIR, "J1_VIIRS_C2_Global_7d.csv")
    FIRMS_J2_PATH: str = os.path.join(DATASET_DIR, "J2_VIIRS_C2_Global_7d.csv")
    FIRMS_SUOMI_PATH: str = os.path.join(DATASET_DIR, "SUOMI_VIIRS_C2_Global_7d.csv")

    # NASA FIRMS API (optional — for live mode)
    FIRMS_API_KEY: str = os.getenv("FIRMS_API_KEY", "")
    FIRMS_DATA_MODE: str = "sample"  # "sample" or "live"

    # Model settings
    ALGERIAN_ARTIFACT_DIR: str = os.path.join(ARTIFACT_DIR, "algerian")
    MESOGEOS_ARTIFACT_DIR: str = os.path.join(ARTIFACT_DIR, "mesogeos")

    # Cache settings
    FIRMS_CACHE_TTL_SECONDS: int = 3600  # 1 hour

    # Prediction thresholds
    ALGERIAN_FIRE_THRESHOLD: float = 0.5
    MESOGEOS_FIRE_THRESHOLD: float = 0.5


settings = Settings()
