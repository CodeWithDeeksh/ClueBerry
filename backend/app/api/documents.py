"""
Document upload and retrieval endpoints.
"""
import uuid
import asyncio
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from app.config import settings
from app.models.document import DocumentMeta, DocumentType, DocumentStatus, DocumentUploadResponse
from app.models.evidence import Evidence
from app.services import storage as storage_svc, evidence_store, extraction
from app.services.evidence_store import update_document_status, save_evidence

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {"pdf", "txt", "eml", "msg"}


def _guess_doc_type(filename: str) -> DocumentType:
    name = filename.lower()
    if "invoice" in name or "inv" in name:
        return DocumentType.INVOICE
    if "receipt" in name or "payment" in name or "paid" in name:
        return DocumentType.RECEIPT
    if "reminder" in name or "overdue" in name:
        return DocumentType.REMINDER
    if name.endswith(".eml") or name.endswith(".msg"):
        return DocumentType.EMAIL
    return DocumentType.UNKNOWN


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    # Validate extension
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type '.{ext}' not supported. Allowed: {ALLOWED_EXTENSIONS}")

    # Validate size
    file_bytes = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_size_mb}MB limit.")

    document_id = f"doc_{uuid.uuid4().hex[:10]}"
    s3_key = f"documents/{document_id}/{file.filename}"

    # Save to S3
    try:
        storage_svc.upload_to_s3(file_bytes, s3_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")

    # Save metadata
    doc = DocumentMeta(
        document_id=document_id,
        filename=file.filename,
        s3_key=s3_key,
        document_type=_guess_doc_type(file.filename),
        status=DocumentStatus.UPLOADED,
    )
    evidence_store.save_document_meta(doc)

    # Trigger async processing
    background_tasks.add_task(_process_document, document_id, file_bytes, file.filename)

    return DocumentUploadResponse(
        document_id=document_id,
        filename=file.filename,
        status=DocumentStatus.PROCESSING,
        message="Document uploaded. Extraction in progress.",
    )


async def _process_document(document_id: str, file_bytes: bytes, filename: str):
    """Background task: extract text → structured fields → save evidence."""
    try:
        update_document_status(document_id, DocumentStatus.PROCESSING)

        # Extract raw text
        text = extraction.extract_text(file_bytes, filename)

        # Try Bedrock structured extraction; fall back to heuristics
        try:
            import boto3
            bedrock = boto3.client(
                "bedrock-runtime",
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )
            fields = extraction.extract_structured_fields(text, bedrock, settings.bedrock_model_id)
        except Exception:
            fields = _heuristic_extract(text, filename)

        # Build evidence record
        doc_meta = evidence_store.get_document_meta(document_id)
        ev = Evidence(
            document_id=document_id,
            source_filename=filename,
            source_location="Page 1",
            document_type=fields.get("document_type") or (doc_meta.document_type.value if doc_meta else "unknown"),
            invoice_number=fields.get("invoice_number"),
            vendor_name=fields.get("vendor_name"),
            amount=fields.get("amount"),
            currency=fields.get("currency", "INR"),
            invoice_date=fields.get("invoice_date"),
            payment_date=fields.get("payment_date"),
            payment_reference=fields.get("payment_reference"),
            payment_status=fields.get("payment_status"),
            evidence_items=[
                type('EvidenceItem', (), item)() if isinstance(item, dict) else item
                for item in fields.get("evidence_items", [])
            ],
        )
        save_evidence(ev)
        update_document_status(document_id, DocumentStatus.READY)

    except Exception as e:
        update_document_status(document_id, DocumentStatus.FAILED, str(e))


def _heuristic_extract(text: str, filename: str) -> dict:
    """Simple regex-based extraction fallback when Bedrock is unavailable."""
    import re
    result = {
        "document_type": _guess_doc_type(filename).value,
        "invoice_number": None,
        "vendor_name": None,
        "amount": None,
        "currency": "INR",
        "invoice_date": None,
        "payment_date": None,
        "payment_reference": None,
        "payment_status": None,
        "evidence_items": [],
    }

    # Invoice number
    inv = re.search(r"(?:invoice|inv)[#\s\-:]*([A-Z0-9\-]+)", text, re.IGNORECASE)
    if inv:
        result["invoice_number"] = inv.group(1).strip()
        result["evidence_items"].append({"field": "invoice_number", "value": inv.group(1), "source_text": inv.group(0)})

    # Amount (INR patterns)
    amt = re.search(r"(?:₹|INR|Rs\.?)\s*([\d,]+(?:\.\d{1,2})?)", text, re.IGNORECASE)
    if amt:
        result["amount"] = float(amt.group(1).replace(",", ""))
        result["evidence_items"].append({"field": "amount", "value": amt.group(1), "source_text": amt.group(0)})

    # Payment reference / TXN
    txn = re.search(r"(?:TXN|REF|reference)[#\s\-:]*([A-Z0-9\-]+)", text, re.IGNORECASE)
    if txn:
        result["payment_reference"] = txn.group(1).strip()

    # Dates
    date = re.search(r"\d{4}-\d{2}-\d{2}", text)
    if date:
        if "invoice" in filename.lower():
            result["invoice_date"] = date.group(0)
        else:
            result["payment_date"] = date.group(0)

    return result


@router.get("", response_model=List[DocumentMeta])
async def list_documents():
    try:
        return evidence_store.list_documents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentMeta)
async def get_document(document_id: str):
    doc = evidence_store.get_document_meta(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc
