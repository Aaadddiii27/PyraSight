"""Health endpoints."""
from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    ms = getattr(request.app.state, "model_service", None)
    return {
        "status": "healthy",
        "version": "1.0.0",
        "models": ms.get_status() if ms else {"algerian_classifier": "unavailable", "mesogeos_hazard": "unavailable"},
        "data_mode": "sample",
    }


@router.get("/health/ready")
async def readiness(request: Request):
    ms = getattr(request.app.state, "model_service", None)
    ready = ms is not None and (ms.algerian_ready or ms.mesogeos_ready)
    return {"ready": ready}
