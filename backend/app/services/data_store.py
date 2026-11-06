"""SQLite-backed persistent data store for PyraSight application records."""

import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class DataStore:
    """Persist predictions, incidents, alerts, alert rules and reports in SQLite."""

    TABLES = ("incidents", "predictions", "alerts", "alert_rules", "reports")

    def __init__(self, db_path: Optional[str] = None):
        # A deterministic absolute path prevents SQLite creating a DB in a
        # different directory depending on the shell's current working folder.
        default_path = Path(__file__).resolve().parents[2] / "data" / "pyrasight.db"
        self.db_path = Path(db_path).resolve() if db_path else default_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()
        logger.info("SQLite data store initialized: %s", self.db_path)

    def _connect(self):
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _initialize(self):
        with self._connect() as conn:
            for table in self.TABLES:
                conn.execute(
                    f"CREATE TABLE IF NOT EXISTS {table} ("
                    "id TEXT PRIMARY KEY, payload TEXT NOT NULL, created_at TEXT NOT NULL)"
                )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_predictions_created ON predictions(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_created ON incidents(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at)")

    @staticmethod
    def _dump(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, default=str)

    @staticmethod
    def _load(value: str) -> Any:
        return json.loads(value)

    def _insert(self, table: str, record: Dict[str, Any]):
        with self._connect() as conn:
            conn.execute(
                f"INSERT OR REPLACE INTO {table} (id, payload, created_at) VALUES (?, ?, ?)",
                (record["id"], self._dump(record), record.get("created_at", record.get("timestamp", _now()))),
            )

    def _get(self, table: str, record_id: str):
        with self._connect() as conn:
            row = conn.execute(f"SELECT payload FROM {table} WHERE id = ?", (record_id,)).fetchone()
        return self._load(row["payload"]) if row else None

    def _all(self, table: str, descending: bool = False):
        order = "DESC" if descending else "ASC"
        with self._connect() as conn:
            rows = conn.execute(f"SELECT payload FROM {table} ORDER BY created_at {order}, rowid {order}").fetchall()
        return [self._load(row["payload"]) for row in rows]

    def _delete(self, table: str, record_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
        return cursor.rowcount > 0

    # Incidents
    def create_incident(self, data: Dict[str, Any]) -> Dict[str, Any]:
        iid, now = str(uuid.uuid4())[:8], _now()
        incident = {
            "id": iid, "title": data["title"], "latitude": data["latitude"],
            "longitude": data["longitude"], "description": data.get("description", ""),
            "source": data.get("source", "manual"), "severity": data.get("severity", "unknown"),
            "status": "new", "created_at": now, "updated_at": now,
            "notes": [], "bookmarked": False,
        }
        self._insert("incidents", incident)
        logger.info("Incident created: %s", iid)
        return incident

    def get_incidents(self, status: Optional[str] = None, bookmarked: Optional[bool] = None) -> List[Dict[str, Any]]:
        results = self._all("incidents", descending=True)
        if status:
            results = [item for item in results if item.get("status") == status]
        if bookmarked is not None:
            results = [item for item in results if item.get("bookmarked") == bookmarked]
        return results

    def get_incident(self, iid: str) -> Optional[Dict[str, Any]]:
        return self._get("incidents", iid)

    def update_incident(self, iid: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        incident = self.get_incident(iid)
        if not incident:
            return None
        allowed = {"title", "latitude", "longitude", "description", "status", "severity", "bookmarked"}
        for key, value in updates.items():
            if key in allowed and value is not None:
                incident[key] = value
        incident["updated_at"] = _now()
        self._insert("incidents", incident)
        return incident

    def delete_incident(self, iid: str) -> bool:
        deleted = self._delete("incidents", iid)
        if deleted:
            logger.info("Incident deleted: %s", iid)
        return deleted

    def add_note(self, iid: str, content: str) -> Optional[Dict[str, Any]]:
        incident = self.get_incident(iid)
        if not incident:
            return None
        note = {"content": content, "timestamp": _now()}
        incident.setdefault("notes", []).append(note)
        incident["updated_at"] = note["timestamp"]
        self._insert("incidents", incident)
        return incident

    # Predictions
    def save_prediction(self, model: str, request: Dict, response: Dict):
        entry = {"id": str(uuid.uuid4())[:8], "model": model, "request": request,
                 "response": response, "timestamp": _now()}
        self._insert("predictions", entry)
        with self._connect() as conn:
            conn.execute("DELETE FROM predictions WHERE id IN (SELECT id FROM predictions ORDER BY created_at DESC, rowid DESC LIMIT -1 OFFSET 500)")
        return entry

    def get_prediction_history(self, model: Optional[str] = None, limit: int = 50) -> List[Dict]:
        results = self._all("predictions", descending=True)
        if model:
            results = [item for item in results if item.get("model") == model]
        return results[:max(0, limit)]

    def prediction_trends(self) -> List[Dict[str, Any]]:
        daily: Dict[str, int] = {}
        for item in self._all("predictions"):
            date = item.get("timestamp", "").split("T")[0]
            if date:
                daily[date] = daily.get(date, 0) + 1
        return [{"date": date, "count": count} for date, count in sorted(daily.items())]

    # Alert rules and alerts
    def create_alert_rule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        rule = {"id": str(uuid.uuid4())[:8], "name": data["name"],
                "rule_type": data["rule_type"], "config": data.get("config", {}),
                "enabled": data.get("enabled", True), "created_at": _now()}
        self._insert("alert_rules", rule)
        return rule

    def fire_alert(self, rule_id: str, message: str, severity: str = "info"):
        rule = self._get("alert_rules", rule_id) or {}
        alert = {"id": str(uuid.uuid4())[:8], "rule_id": rule_id,
                 "name": rule.get("name", "Unknown"), "rule_type": rule.get("rule_type", ""),
                 "message": message, "severity": severity, "created_at": _now(), "acknowledged": False}
        self._insert("alerts", alert)
        with self._connect() as conn:
            conn.execute("DELETE FROM alerts WHERE id IN (SELECT id FROM alerts ORDER BY created_at DESC, rowid DESC LIMIT -1 OFFSET 200)")
        return alert

    def get_alerts(self, limit: int = 50) -> List[Dict]:
        return self._all("alerts", descending=True)[:max(0, limit)]

    def get_alert_rules(self) -> List[Dict]:
        return self._all("alert_rules", descending=True)

    # Reports (content is stored with the report so downloads survive restarts)
    def create_report(self, data: Dict[str, Any], content: Any = None) -> Dict[str, Any]:
        rid = str(uuid.uuid4())[:8]
        report = {"id": rid, "title": data.get("title") or f"Report {rid}",
                  "report_type": data["report_type"], "created_at": _now(),
                  "status": "ready", "content": content,
                  "download_url": f"/api/v1/reports/{rid}/download"}
        self._insert("reports", report)
        return report

    def get_report(self, rid: str) -> Optional[Dict[str, Any]]:
        return self._get("reports", rid)

    def get_reports(self) -> List[Dict[str, Any]]:
        return self._all("reports", descending=True)

    # Summary
    def history_summary(self) -> Dict[str, Any]:
        predictions = self._all("predictions")
        return {"total_predictions": len(predictions),
                "algerian_predictions": sum(1 for p in predictions if p.get("model") == "algerian"),
                "mesogeos_predictions": sum(1 for p in predictions if p.get("model") == "mesogeos"),
                "total_incidents": len(self._all("incidents")),
                "total_alerts": len(self._all("alerts"))}
