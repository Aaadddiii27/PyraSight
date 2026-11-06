"""
PyraSight FastAPI Backend Application
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.v1.router import api_router
from app.services.model_service import ModelService
from app.services.firms_service import FIRMSService
from app.services.data_store import DataStore

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - load models and data on startup."""
    logger.info("PyraSight backend starting...")

    # Data store
    app.state.data_store = DataStore(settings.DATABASE_PATH)

    # ML models
    try:
        model_service = ModelService()
        model_service.load_all_models()
        app.state.model_service = model_service
        logger.info("Models loaded successfully")
    except Exception as e:
        logger.warning(f"Model loading failed: {e}")
        app.state.model_service = None

    # FIRMS data
    try:
        firms = FIRMSService(settings.DATASET_DIR)
        firms.load()
        app.state.firms_service = firms
        logger.info(f"FIRMS data loaded: {len(firms.detections):,} detections")
    except Exception as e:
        logger.warning(f"FIRMS loading failed: {e}")
        app.state.firms_service = None

    yield
    logger.info("PyraSight backend shutting down.")


app = FastAPI(
    title="PyraSight API",
    description="Wildfire Intelligence, Prediction & Monitoring Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "PyraSight API", "docs": "/api/docs", "version": "1.0.0"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__}
    )
