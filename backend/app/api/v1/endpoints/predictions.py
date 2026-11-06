"""Prediction endpoints for both models."""
from fastapi import APIRouter, Request, HTTPException
from app.schemas.schemas import (
    AlgerianPredictionRequest, AlgerianPredictionResponse,
    MesogeosPredictionRequest, MesogeosPredictionResponse,
)

router = APIRouter()


def _get_services(request: Request):
    ms = getattr(request.app.state, "model_service", None)
    ds = getattr(request.app.state, "data_store", None)
    return ms, ds


@router.post("/algerian", response_model=AlgerianPredictionResponse)
async def predict_algerian(body: AlgerianPredictionRequest, request: Request):
    ms, ds = _get_services(request)
    if not ms or not ms.algerian_ready:
        raise HTTPException(503, "Algerian model not available")
    features = body.model_dump()
    result = ms.algerian.predict(features)
    if ds:
        ds.save_prediction("algerian", features, result)
    return result


@router.get("/algerian/history")
async def algerian_history(request: Request):
    ds = getattr(request.app.state, "data_store", None)
    if not ds:
        return []
    return ds.get_prediction_history(model="algerian")


@router.post("/mesogeos", response_model=MesogeosPredictionResponse)
async def predict_mesogeos(body: MesogeosPredictionRequest, request: Request):
    ms, ds = _get_services(request)
    if not ms or not ms.mesogeos_ready:
        raise HTTPException(503, "Mesogeos model not available")
    features = body.model_dump()
    result = ms.mesogeos.predict(features)
    if ds:
        ds.save_prediction("mesogeos", features, result)
    return result


@router.get("/mesogeos/history")
async def mesogeos_history(request: Request):
    ds = getattr(request.app.state, "data_store", None)
    if not ds:
        return []
    return ds.get_prediction_history(model="mesogeos")
