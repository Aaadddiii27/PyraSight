"""Incident management endpoints."""
from fastapi import APIRouter, Request, HTTPException
from typing import Optional
from app.schemas.schemas import IncidentCreate, IncidentNote, IncidentUpdate

router = APIRouter()


def _ds(request: Request):
    return getattr(request.app.state, "data_store", None)


@router.get("")
async def list_incidents(request: Request, status: Optional[str] = None, bookmarked: Optional[bool] = None):
    ds = _ds(request)
    if not ds:
        return []
    return ds.get_incidents(status=status, bookmarked=bookmarked)


@router.post("")
async def create_incident(body: IncidentCreate, request: Request):
    ds = _ds(request)
    if not ds:
        raise HTTPException(503, "Data store unavailable")
    return ds.create_incident(body.model_dump())


@router.get("/{incident_id}")
async def get_incident(incident_id: str, request: Request):
    ds = _ds(request)
    if not ds:
        raise HTTPException(503, "Data store unavailable")
    inc = ds.get_incident(incident_id)
    if not inc:
        raise HTTPException(404, "Incident not found")
    return inc


@router.patch("/{incident_id}")
async def update_incident(incident_id: str, body: IncidentUpdate, request: Request):
    ds = _ds(request)
    if not ds:
        raise HTTPException(503, "Data store unavailable")
    result = ds.update_incident(incident_id, body.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(404, "Incident not found")
    return result


@router.post("/{incident_id}/notes")
async def add_note(incident_id: str, body: IncidentNote, request: Request):
    ds = _ds(request)
    if not ds:
        raise HTTPException(503, "Data store unavailable")
    result = ds.add_note(incident_id, body.content)
    if not result:
        raise HTTPException(404, "Incident not found")
    return result
@router.delete("/{incident_id}")
async def delete_incident(incident_id: str, request: Request):
    ds = _ds(request)

    if not ds:
        raise HTTPException(503, "Data store unavailable")

    deleted = ds.delete_incident(incident_id)

    if not deleted:
        raise HTTPException(404, "Incident not found")

    return {
        "message": "Incident deleted successfully",
        "id": incident_id,
    }
