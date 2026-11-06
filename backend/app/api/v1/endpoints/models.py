"""Model information endpoints."""
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()


@router.get("")
async def list_models(request: Request):
    ms = getattr(request.app.state, "model_service", None)
    if not ms:
        return []
    models = []
    if ms.algerian_ready:
        models.append(ms.algerian.get_model_info())
    else:
        models.append({"model_id": "algerian_classifier", "status": "unavailable"})
    if ms.mesogeos_ready:
        models.append(ms.mesogeos.get_model_info())
    else:
        models.append({"model_id": "mesogeos_hazard", "status": "unavailable"})
    return models


@router.get("/{model_id}/metrics")
async def model_metrics(model_id: str, request: Request):
    ms = getattr(request.app.state, "model_service", None)
    if not ms:
        raise HTTPException(503, "Models not loaded")
    if model_id == "algerian_classifier":
        if not ms.algerian_ready:
            raise HTTPException(503, "Algerian model not available")
        info = ms.algerian.get_model_info()
        return {"model_id": model_id, **info.get("evaluation", {})}
    elif model_id == "mesogeos_hazard":
        if not ms.mesogeos_ready:
            raise HTTPException(503, "Mesogeos model not available")
        info = ms.mesogeos.get_model_info()
        return {"model_id": model_id, **info.get("evaluation", {})}
    raise HTTPException(404, f"Unknown model: {model_id}")


@router.get("/{model_id}/explanations")
async def model_explanations(model_id: str, request: Request):
    ms = getattr(request.app.state, "model_service", None)
    if not ms:
        raise HTTPException(503, "Models not loaded")
    if model_id == "algerian_classifier":
        if not ms.algerian_ready:
            raise HTTPException(503, "Model not available")
        fi = ms.algerian.feature_importance or {}
        return {"model_id": model_id, "method": fi.get("method", "none"), "feature_importance": fi.get("feature_importance", {})}
    elif model_id == "mesogeos_hazard":
        if not ms.mesogeos_ready:
            raise HTTPException(503, "Model not available")
        fi = ms.mesogeos.feature_importance or {}
        return {"model_id": model_id, "method": fi.get("method", "none"), "feature_importance": fi.get("feature_importance", {})}
    raise HTTPException(404, f"Unknown model: {model_id}")
