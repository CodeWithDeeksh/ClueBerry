from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import uuid

class InvestigationStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"

class MatchStatus(str, Enum):
    STRONG_MATCH = "strong_match"
    POSSIBLE_MATCH = "possible_match"
    AMOUNT_MISMATCH = "amount_mismatch"
    PARTIAL_PAYMENT = "partial_payment_possible"
    NO_EVIDENCE = "no_payment_evidence_found"
    CONFLICTING = "conflicting_records"

class MCPToolCall(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    result_summary: str
    evidence_ids: List[str] = []
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class TimelineEntry(BaseModel):
    date: Optional[str]
    event: str
    document_id: str
    source_filename: str
    evidence_id: Optional[str] = None

class InvestigationReport(BaseModel):
    finding: str
    summary: str
    match_status: MatchStatus
    evidence_list: List[Dict[str, Any]] = []
    contradictions: List[str] = []
    timeline: List[TimelineEntry] = []
    confidence_note: str = ""
    draft_response: str = ""

class InvestigationRequest(BaseModel):
    question: str
    document_ids: List[str]

class InvestigationRecord(BaseModel):
    investigation_id: str = Field(default_factory=lambda: f"inv_{uuid.uuid4().hex[:8]}")
    question: str
    document_ids: List[str]
    status: InvestigationStatus = InvestigationStatus.QUEUED
    mcp_tool_calls: List[MCPToolCall] = []
    report: Optional[InvestigationReport] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    error: Optional[str] = None

class InvestigationResponse(BaseModel):
    investigation_id: str
    status: InvestigationStatus
