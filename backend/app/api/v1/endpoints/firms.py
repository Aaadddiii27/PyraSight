"""FIRMS satellite detection endpoints."""
from fastapi import APIRouter, Request, Query
from typing import Optional

router = APIRouter()


def _get_firms(request: Request):
    return getattr(request.app.state, "firms_service", None)


@router.get("/detections")
async def get_detections(
    request: Request,
    satellite: Optional[str] = None,
    confidence: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    min_lat: Optional[float] = None,
    max_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lon: Optional[float] = None,
    daynight: Optional[str] = None,
    limit: int = Query(5000, ge=1, le=50000),
    offset: int = Query(0, ge=0),
):
    fs = _get_firms(request)
    if not fs:
        return {"detections": [], "total": 0, "source": "none", "date_range": {}, "data_mode": "unavailable"}
    results, total = fs.query(
        satellite=satellite, confidence=confidence,
        date_from=date_from, date_to=date_to,
        min_lat=min_lat, max_lat=max_lat,
        min_lon=min_lon, max_lon=max_lon,
        daynight=daynight, limit=limit, offset=offset,
    )
    dates = sorted(set(d["acq_date"] for d in results if d.get("acq_date")))
    return {
        "detections": results,
        "total": total,
        "returned": len(results),
        "source": "NASA FIRMS VIIRS C2 (sample files)",
        "date_range": {"min": dates[0] if dates else "", "max": dates[-1] if dates else ""},
        "data_mode": "sample",
    }


@router.get("/status")
async def firms_status(request: Request):
    fs = _get_firms(request)
    if not fs:
        return {"data_mode": "unavailable", "total_detections": 0, "files_available": {}}
    return fs.status()


@router.get("/summary")
async def firms_summary(request: Request):
    fs = _get_firms(request)
    if not fs:
        return {"total_detections": 0, "by_satellite": {}, "by_confidence": {}, "by_daynight": {}, "date_range": {}, "data_mode": "unavailable"}
    return fs.summary()


@router.get("/trends")
async def firms_trends(request: Request):
    fs = _get_firms(request)
    if not fs:
        return []
    return fs.trends()
