"""
Investigation endpoints.
"""
import threading
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.investigation import (
    InvestigationRequest, InvestigationResponse, InvestigationRecord,
    InvestigationStatus, InvestigationReport,
)
from app.services import investigation as inv_svc
from app.services import storage as storage_svc
from datetime import datetime

router = APIRouter(prefix="/investigations", tags=["investigations"])

# In-memory store for MVP (replace with DynamoDB in production)
_investigations: dict[str, InvestigationRecord] = {}


@router.post("", response_model=InvestigationResponse)
async def start_investigation(
    request: InvestigationRequest,
    background_tasks: BackgroundTasks,
):
    record = InvestigationRecord(
        question=request.question,
        document_ids=request.document_ids,
        status=InvestigationStatus.QUEUED,
    )
    _investigations[record.investigation_id] = record

    # Persist to DynamoDB
    try:
        storage_svc.put_item(
            pk=f"INV#{record.investigation_id}",
            sk="META",
            data=record.model_dump(mode="json"),
        )
    except Exception:
        pass  # Continue even if DynamoDB unavailable in dev

    background_tasks.add_task(_run_investigation_bg, record.investigation_id)

    return InvestigationResponse(
        investigation_id=record.investigation_id,
        status=record.status,
    )


def _run_investigation_bg(investigation_id: str):
    record = _investigations.get(investigation_id)
    if not record:
        return
    updated = inv_svc.run_investigation(record)
    _investigations[investigation_id] = updated

    # Persist result
    try:
        storage_svc.put_item(
            pk=f"INV#{investigation_id}",
            sk="META",
            data=updated.model_dump(mode="json"),
        )
        if updated.report:
            storage_svc.put_item(
                pk=f"INV#{investigation_id}",
                sk="REPORT",
                data=updated.report.model_dump(mode="json"),
            )
    except Exception:
        pass


@router.get("/{investigation_id}", response_model=InvestigationRecord)
async def get_investigation(investigation_id: str):
    record = _investigations.get(investigation_id)
    if not record:
        # Try DynamoDB
        try:
            item = storage_svc.get_item(f"INV#{investigation_id}", "META")
            if item:
                record = InvestigationRecord(**{k: v for k, v in item.items() if k not in ("PK", "SK")})
                _investigations[investigation_id] = record
        except Exception:
            pass
    if not record:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return record


@router.get("/{investigation_id}/report", response_model=InvestigationReport)
async def get_report(investigation_id: str):
    record = _investigations.get(investigation_id)
    if not record or not record.report:
        raise HTTPException(status_code=404, detail="Report not ready yet")
    return record.report
