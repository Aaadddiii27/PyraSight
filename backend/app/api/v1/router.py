"""PyraSight — API v1 Router — aggregates all endpoint sub-routers."""

from fastapi import APIRouter
from app.api.v1.endpoints import health, predictions, firms, models, incidents, alerts, reports, history

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
api_router.include_router(firms.router, prefix="/firms", tags=["FIRMS"])
api_router.include_router(models.router, prefix="/models", tags=["Models"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(history.router, prefix="/history", tags=["History"])
