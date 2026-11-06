"""PyraSight — FIRMS Data Service. Loads and queries NASA FIRMS CSV data."""

import os
import csv
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FIRMSService:
    """Manages NASA FIRMS satellite fire detection data."""

    def __init__(self, dataset_dir: str):
        self.dataset_dir = dataset_dir
        self.detections: List[Dict[str, Any]] = []
        self.loaded = False
        self.load_timestamp: Optional[str] = None
        self.files_status: Dict[str, bool] = {}

    def load(self):
        """Load all FIRMS CSV files from disk."""
        files = {
            "J1_VIIRS_C2": os.path.join(self.dataset_dir, "J1_VIIRS_C2_Global_7d.csv"),
            "J2_VIIRS_C2": os.path.join(self.dataset_dir, "J2_VIIRS_C2_Global_7d.csv"),
            "SUOMI_VIIRS_C2": os.path.join(self.dataset_dir, "SUOMI_VIIRS_C2_Global_7d.csv"),
        }
        self.detections = []
        for product, path in files.items():
            exists = os.path.exists(path)
            self.files_status[product] = exists
            if not exists:
                logger.warning(f"FIRMS file missing: {path}")
                continue
            try:
                count = 0
                with open(path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            det = {
                                "latitude": float(row.get("latitude", 0)),
                                "longitude": float(row.get("longitude", 0)),
                                "bright_ti4": _safe_float(row.get("bright_ti4")),
                                "bright_ti5": _safe_float(row.get("bright_ti5")),
                                "scan": _safe_float(row.get("scan")),
                                "track": _safe_float(row.get("track")),
                                "acq_date": row.get("acq_date", ""),
                                "acq_time": row.get("acq_time", ""),
                                "satellite": row.get("satellite", ""),
                                "confidence": row.get("confidence", ""),
                                "version": row.get("version", ""),
                                "frp": _safe_float(row.get("frp")),
                                "daynight": row.get("daynight", ""),
                                "product": product,
                            }
                            self.detections.append(det)
                            count += 1
                        except Exception:
                            continue
                logger.info(f"Loaded {count:,} detections from {product}")
            except Exception as e:
                logger.error(f"Failed to load {product}: {e}")

        self.loaded = True
        self.load_timestamp = datetime.utcnow().isoformat() + "Z"
        logger.info(f"FIRMS total: {len(self.detections):,} detections loaded")

    def query(
        self,
        satellite: Optional[str] = None,
        confidence: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None,
        daynight: Optional[str] = None,
        limit: int = 5000,
        offset: int = 0,
    ) -> tuple[List[Dict[str, Any]], int]:
        """Query detections with filters. Returns (results, total_matching)."""
        if not self.loaded:
            self.load()

        filtered = self.detections
        if satellite:
            filtered = [d for d in filtered if d["satellite"] == satellite or d["product"].startswith(satellite.upper().replace("-", "_").replace(" ", "_"))]
        if confidence:
            filtered = [d for d in filtered if d["confidence"] == confidence]
        if date_from:
            filtered = [d for d in filtered if d["acq_date"] >= date_from]
        if date_to:
            filtered = [d for d in filtered if d["acq_date"] <= date_to]
        if min_lat is not None:
            filtered = [d for d in filtered if d["latitude"] >= min_lat]
        if max_lat is not None:
            filtered = [d for d in filtered if d["latitude"] <= max_lat]
        if min_lon is not None:
            filtered = [d for d in filtered if d["longitude"] >= min_lon]
        if max_lon is not None:
            filtered = [d for d in filtered if d["longitude"] <= max_lon]
        if daynight:
            filtered = [d for d in filtered if d["daynight"] == daynight]

        total = len(filtered)
        return filtered[offset: offset + limit], total

    def summary(self) -> Dict[str, Any]:
        """Return summary statistics about loaded FIRMS data."""
        if not self.loaded:
            self.load()

        by_satellite: Dict[str, int] = {}
        by_confidence: Dict[str, int] = {}
        by_daynight: Dict[str, int] = {}
        dates = set()

        for d in self.detections:
            sat = d["satellite"]
            by_satellite[sat] = by_satellite.get(sat, 0) + 1
            conf = d["confidence"]
            by_confidence[conf] = by_confidence.get(conf, 0) + 1
            dn = d["daynight"]
            by_daynight[dn] = by_daynight.get(dn, 0) + 1
            if d["acq_date"]:
                dates.add(d["acq_date"])

        sorted_dates = sorted(dates) if dates else []
        return {
            "total_detections": len(self.detections),
            "by_satellite": by_satellite,
            "by_confidence": by_confidence,
            "by_daynight": by_daynight,
            "date_range": {
                "min": sorted_dates[0] if sorted_dates else "",
                "max": sorted_dates[-1] if sorted_dates else "",
            },
            "data_mode": "sample",
        }

    def status(self) -> Dict[str, Any]:
        return {
            "data_mode": "sample",
            "last_loaded": self.load_timestamp,
            "files_available": self.files_status,
            "total_detections": len(self.detections),
        }

    def trends(self) -> List[Dict[str, Any]]:
        """Daily detection counts by satellite."""
        if not self.loaded:
            self.load()
        counts: Dict[str, Dict[str, int]] = {}
        for d in self.detections:
            date = d["acq_date"]
            sat = d["satellite"]
            key = f"{date}|{sat}"
            if key not in counts:
                counts[key] = {"date": date, "satellite": sat, "count": 0}
            counts[key]["count"] += 1
        return sorted(counts.values(), key=lambda x: (x["date"], x["satellite"]))


def _safe_float(val) -> Optional[float]:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
