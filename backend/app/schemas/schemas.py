"""PyraSight — Pydantic Schemas for API payloads."""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# --- Health ---
class HealthResponse(BaseModel):
    status: str
    version: str
    models: Dict[str, str]
    data_mode: str


# --- Algerian Prediction ---
class AlgerianPredictionRequest(BaseModel):
    Temperature: float = Field(..., ge=-10, le=60, description="Temperature in Celsius")
    Ws: float = Field(..., ge=0, le=100, description="Wind speed in km/h")
    Rain: float = Field(..., ge=0, le=200, description="Rainfall in mm")
    RH: float = Field(..., ge=0, le=100, description="Relative Humidity %")
    FFMC: float = Field(..., ge=0, le=101, description="Fine Fuel Moisture Code")
    DMC: float = Field(..., ge=0, le=300, description="Duff Moisture Code")
    DC: float = Field(..., ge=0, le=900, description="Drought Code")
    ISI: float = Field(..., ge=0, le=60, description="Initial Spread Index")
    BUI: float = Field(..., ge=0, le=300, description="Buildup Index")
    FWI: float = Field(..., ge=0, le=150, description="Fire Weather Index")


class FeatureContribution(BaseModel):
    feature: str
    value: float
    importance: float
    direction: str


class AlgerianPredictionResponse(BaseModel):
    prediction: int
    label: str
    probability_fire: float
    probability_no_fire: float
    risk_level: str
    threshold: float
    model_type: str
    feature_contributions: List[FeatureContribution]
    disclaimer: str


# --- Mesogeos Prediction ---
class MesogeosPredictionRequest(BaseModel):
    aspect: float = Field(0, description="Terrain aspect (degrees)")
    curvature: float = Field(0, description="Terrain curvature")
    d2m: float = Field(280, description="Dewpoint temperature 2m (K)")
    dem: float = Field(500, description="Digital elevation model (m)")
    lai: float = Field(1, description="Leaf area index")
    lst_day: float = Field(300, description="Land surface temp day (K)")
    lst_night: float = Field(285, description="Land surface temp night (K)")
    ndvi: float = Field(0.4, description="NDVI vegetation index")
    rh: float = Field(0.4, description="Relative humidity (0-1)")
    roads_distance: float = Field(3, description="Distance to roads (km)")
    slope: float = Field(0.5, description="Terrain slope (rad)")
    smi: float = Field(0.5, description="Soil moisture index (0-1)")
    sp: float = Field(95000, description="Surface pressure (Pa)")
    ssrd: float = Field(10000000, description="Surface solar radiation (J/m2)")
    t2m: float = Field(295, description="Temperature 2m (K)")
    tp: float = Field(0, description="Total precipitation (m)")
    wind_direction: float = Field(180, description="Wind direction (degrees)")
    wind_speed: float = Field(3, description="Wind speed (m/s)")
    lc_agriculture: float = Field(0, ge=0, le=1, description="Land cover: agriculture fraction")
    lc_forest: float = Field(0, ge=0, le=1, description="Land cover: forest fraction")
    lc_grassland: float = Field(0, ge=0, le=1, description="Land cover: grassland fraction")
    lc_settlement: float = Field(0, ge=0, le=1, description="Land cover: settlement fraction")
    lc_shrubland: float = Field(0, ge=0, le=1, description="Land cover: shrubland fraction")
    lc_sparse_vegetation: float = Field(0, ge=0, le=1, description="Land cover: sparse vegetation fraction")
    lc_water_bodies: float = Field(0, ge=0, le=1, description="Land cover: water bodies fraction")
    lc_wetland: float = Field(0, ge=0, le=1, description="Land cover: wetland fraction")
    population: float = Field(0, ge=0, description="Population density")


class MesogeosPredictionResponse(BaseModel):
    prediction: int
    label: str
    probability_danger: float
    probability_safe: float
    danger_level: str
    model_type: str
    feature_contributions: List[Dict[str, Any]]
    disclaimer: str


# --- FIRMS ---
class FIRMSDetection(BaseModel):
    latitude: float
    longitude: float
    bright_ti4: Optional[float] = None
    bright_ti5: Optional[float] = None
    scan: Optional[float] = None
    track: Optional[float] = None
    acq_date: str
    acq_time: str
    satellite: str
    confidence: str
    version: str
    frp: Optional[float] = None
    daynight: str
    product: str


class FIRMSResponse(BaseModel):
    detections: List[FIRMSDetection]
    total: int
    source: str
    date_range: Dict[str, str]
    data_mode: str


class FIRMSSummary(BaseModel):
    total_detections: int
    by_satellite: Dict[str, int]
    by_confidence: Dict[str, int]
    by_daynight: Dict[str, int]
    date_range: Dict[str, str]
    data_mode: str


class FIRMSStatus(BaseModel):
    data_mode: str
    last_loaded: Optional[str] = None
    files_available: Dict[str, bool]
    total_detections: int


# --- Models ---
class ModelInfo(BaseModel):
    model_id: str
    model_type: Optional[str] = None
    dataset: Optional[str] = None
    n_train: Optional[int] = None
    n_test: Optional[int] = None
    features: Optional[List[str]] = None
    target: Optional[str] = None
    geographic_scope: Optional[str] = None
    status: str
    evaluation: Optional[Dict[str, Any]] = None


class ModelMetrics(BaseModel):
    model_id: str
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1: Optional[float] = None
    roc_auc: Optional[float] = None
    pr_auc: Optional[float] = None
    confusion_matrix: Optional[List[List[int]]] = None


# --- Incidents ---
class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    latitude: float
    longitude: float
    description: Optional[str] = None
    source: str = "manual"
    severity: str = "unknown"


class IncidentNote(BaseModel):
    content: str = Field(..., min_length=1)


class IncidentResponse(BaseModel):
    id: str
    title: str
    latitude: float
    longitude: float
    description: Optional[str] = None
    source: str
    severity: str
    status: str
    created_at: str
    updated_at: str
    notes: List[Dict[str, str]]
    bookmarked: bool


class IncidentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    description: Optional[str] = None
    status: Optional[str] = None
    severity: Optional[str] = None
    bookmarked: Optional[bool] = None


# --- Alerts ---
class AlertRuleCreate(BaseModel):
    name: str
    rule_type: str  # "region_detection", "hazard_threshold", "data_freshness"
    config: Dict[str, Any]
    enabled: bool = True


class AlertResponse(BaseModel):
    id: str
    name: str
    rule_type: str
    message: str
    severity: str
    created_at: str
    acknowledged: bool


# --- Reports ---
class ReportRequest(BaseModel):
    report_type: str  # "firms_summary", "prediction_history", "incident_report"
    title: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    id: str
    title: str
    report_type: str
    created_at: str
    status: str
    download_url: Optional[str] = None


# --- History ---
class HistorySummary(BaseModel):
    total_predictions: int
    algerian_predictions: int
    mesogeos_predictions: int
    total_incidents: int
    total_firms_detections: int


class TrendPoint(BaseModel):
    date: str
    count: int
    satellite: Optional[str] = None
