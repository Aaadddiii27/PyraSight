"""Alert endpoints."""
from fastapi import APIRouter, Request, HTTPException
from app.schemas.schemas import AlertRuleCreate

router = APIRouter()


@router.get("")
async def list_alerts(request: Request):
    ds = getattr(request.app.state, "data_store", None)
    if not ds:
        return []
    return ds.get_alerts()


@router.post("/rules")
async def create_alert_rule(body: AlertRuleCreate, request: Request):
    ds = getattr(request.app.state, "data_store", None)
    if not ds:
        raise HTTPException(503, "Data store unavailable")
    return ds.create_alert_rule(body.model_dump())


@router.get("/rules")
async def list_alert_rules(request: Request):
    ds = getattr(request.app.state, "data_store", None)
    if not ds:
        return []
    return ds.get_alert_rules()
