from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime
import uuid

class DocumentStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"

class DocumentType(str, Enum):
    INVOICE = "invoice"
    RECEIPT = "receipt"
    REMINDER = "reminder"
    EMAIL = "email"
    UNKNOWN = "unknown"

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: DocumentStatus
    message: str = ""

class DocumentMeta(BaseModel):
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    s3_key: str
    document_type: DocumentType = DocumentType.UNKNOWN
    status: DocumentStatus = DocumentStatus.UPLOADED
    upload_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    extracted_fields: Optional[dict] = None
    error: Optional[str] = None
