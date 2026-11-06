
"""History and trends endpoints."""
from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/summary")
async def history_summary(request: Request):
    ds = getattr(request.app.state, "data_store", None)
    fs = getattr(request.app.state, "firms_service", None)

    summary = ds.history_summary() if ds else {
        "total_predictions": 0,
        "algerian_predictions": 0,
        "mesogeos_predictions": 0,
        "total_incidents": 0,
        "total_alerts": 0,
    }

    summary["total_firms_detections"] = (
        len(fs.detections) if fs and fs.loaded else 0
    )

    return summary


@router.get("/trends")
async def history_trends(request: Request):
    ds = getattr(request.app.state, "data_store", None)

    if not ds:
        return []

    return ds.prediction_trends()
