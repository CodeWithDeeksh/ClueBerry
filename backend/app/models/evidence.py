from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

class EvidenceItem(BaseModel):
    field: str
    value: Optional[str] = None
    source_text: Optional[str] = None

class Evidence(BaseModel):
    evidence_id: str = Field(default_factory=lambda: f"ev_{uuid.uuid4().hex[:8]}")
    document_id: str
    source_filename: str
    source_location: Optional[str] = None

    # Extracted fields
    document_type: Optional[str] = None
    invoice_number: Optional[str] = None
    vendor_name: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = "INR"
    invoice_date: Optional[str] = None
    payment_date: Optional[str] = None
    payment_reference: Optional[str] = None
    payment_status: Optional[str] = None

    evidence_items: List[EvidenceItem] = []
    extraction_confidence: Optional[float] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
