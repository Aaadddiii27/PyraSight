
"""Report generation and download endpoints."""

import csv
import io
import json
import re

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.schemas import ReportRequest

router = APIRouter()


def _build_report_content(report_type, ds, fs):
    """Build report content for each frontend-supported report type."""

    if report_type in ("fire_activity", "firms_summary"):
        if not fs:
            raise HTTPException(503, "FIRMS data service unavailable")

        if report_type == "fire_activity":
            content = fs.trends()
        else:
            content = fs.summary()

    elif report_type == "detection_summary":
        if not fs:
            raise HTTPException(503, "FIRMS data service unavailable")

        content = fs.summary()

    elif report_type in ("model_predictions", "prediction_history"):
        content = ds.get_prediction_history(limit=500)

    elif report_type in ("incident_summary", "incident_report"):
        content = ds.get_incidents()

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported report type: {report_type}",
        )

    # Empty datasets should still produce downloadable reports.
    if isinstance(content, list) and not content:
        return {
            "message": "No records were available when this report was generated.",
            "report_type": report_type,
            "records": [],
        }

    return content


@router.post("")
async def create_report(body: ReportRequest, request: Request):
    ds = getattr(request.app.state, "data_store", None)
    fs = getattr(request.app.state, "firms_service", None)

    if not ds:
        raise HTTPException(503, "Data store unavailable")

    content = _build_report_content(body.report_type, ds, fs)

    report_data = body.model_dump()
    report_data["title"] = (
        body.title.strip()
        if body.title and body.title.strip()
        else None
    )

    return ds.create_report(report_data, content)


@router.get("")
async def list_reports(request: Request):
    ds = getattr(request.app.state, "data_store", None)

    if not ds:
        return []

    return ds.get_reports()


@router.get("/{report_id}")
async def get_report(report_id: str, request: Request):
    ds = getattr(request.app.state, "data_store", None)

    if not ds:
        raise HTTPException(503, "Data store unavailable")

    report = ds.get_report(report_id)

    if not report:
        raise HTTPException(404, "Report not found")

    return report


@router.get("/{report_id}/download")
async def download_report(report_id: str, request: Request):
    ds = getattr(request.app.state, "data_store", None)

    if not ds:
        raise HTTPException(503, "Data store unavailable")

    report = ds.get_report(report_id)

    if not report:
        raise HTTPException(404, "Report not found")

    content = report.get("content")

    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "", report_id)

    if isinstance(content, list) and content:
        if all(isinstance(item, dict) for item in content):
            output = io.StringIO()

            # Include the union of fields from all records.
            fieldnames = list(
                dict.fromkeys(
                    key
                    for item in content
                    for key in item.keys()
                )
            )

            writer = csv.DictWriter(
                output,
                fieldnames=fieldnames,
                extrasaction="ignore",
            )
            writer.writeheader()

            for item in content:
                row = {
                    key: (
                        json.dumps(value, default=str)
                        if isinstance(value, (dict, list))
                        else value
                    )
                    for key, value in item.items()
                }
                writer.writerow(row)

            output_bytes = output.getvalue().encode("utf-8-sig")

            return StreamingResponse(
                io.BytesIO(output_bytes),
                media_type="text/csv",
                headers={
                    "Content-Disposition":
                    f'attachment; filename="pyrasight_report_{safe_id}.csv"'
                },
            )

    if isinstance(content, (dict, list)):
        output_bytes = json.dumps(
            content,
            indent=2,
            default=str,
        ).encode("utf-8")

        return StreamingResponse(
            io.BytesIO(output_bytes),
            media_type="application/json",
            headers={
                "Content-Disposition":
                f'attachment; filename="pyrasight_report_{safe_id}.json"'
            },
        )

    raise HTTPException(
        500,
        "Report content is missing or invalid",
    )
