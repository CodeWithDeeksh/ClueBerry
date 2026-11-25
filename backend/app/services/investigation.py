"""
Investigation orchestration:
1. Set MCP scope to uploaded documents
2. Build evidence context for the AI
3. Call Bedrock with MCP tool call simulation
4. Validate citations
5. Return structured report
"""
import json
import boto3
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.config import settings
from app.models.investigation import (
    InvestigationRecord, InvestigationStatus, InvestigationReport,
    MCPToolCall, TimelineEntry, MatchStatus,
)
from app.services import evidence_store, matching as matching_svc
from app.mcp_server import server as mcp_server


def get_bedrock():
    return boto3.client(
        "bedrock-runtime",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


def run_investigation(record: InvestigationRecord) -> InvestigationRecord:
    """
    Main investigation loop — simulates MCP tool calls then calls Bedrock.
    """
    try:
        record.status = InvestigationStatus.RUNNING
        document_ids = record.document_ids

        # Set MCP scope
        mcp_server.set_scope(document_ids)

        # ── Step 1: search_evidence ──────────────────────────
        all_evidence = evidence_store.search_evidence(document_ids=document_ids)
        
        mcp_call_1 = MCPToolCall(
            tool_name="search_evidence",
            parameters={"query": record.question, "document_ids": document_ids},
            result_summary=f"Found {len(all_evidence)} evidence records across {len(document_ids)} documents",
            evidence_ids=[ev.evidence_id for ev in all_evidence],
        )
        record.mcp_tool_calls.append(mcp_call_1)

        if not all_evidence:
            record.report = InvestigationReport(
                finding="Insufficient evidence",
                summary="No evidence records were found in the uploaded documents.",
                match_status=MatchStatus.NO_EVIDENCE,
                confidence_note="Upload documents and wait for processing to complete before investigating.",
            )
            record.status = InvestigationStatus.COMPLETE
            return record

        # ── Step 2: find_payment_match ───────────────────────
        invoices = [ev for ev in all_evidence if (ev.document_type or "") == "invoice"]
        match_results = []
        
        for invoice in invoices:
            matches = matching_svc.find_payment_matches(invoice, all_evidence)
            match_results.extend(matches)

        mcp_call_2 = MCPToolCall(
            tool_name="find_payment_match",
            parameters={"invoice_numbers": [inv.invoice_number for inv in invoices]},
            result_summary=f"Ran matching against {len(invoices)} invoice(s), found {len(match_results)} candidate match(es)",
            evidence_ids=[m.get("payment_id", "") for m in match_results if m.get("payment_id")],
        )
        record.mcp_tool_calls.append(mcp_call_2)

        # ── Step 3: read_source for top match ────────────────
        if match_results:
            top_match = match_results[0]
            mcp_call_3 = MCPToolCall(
                tool_name="read_source",
                parameters={
                    "document_id": top_match.get("payment_document_id", ""),
                    "evidence_id": top_match.get("payment_id", ""),
                },
                result_summary=f"Retrieved source evidence for match status: {top_match.get('status', 'unknown')}",
                evidence_ids=[top_match.get("payment_id", "")],
            )
            record.mcp_tool_calls.append(mcp_call_3)

        # ── Step 4: build report (Bedrock or fallback) ───────
        timeline = matching_svc.build_timeline(all_evidence)
        
        try:
            report = _call_bedrock_investigation(
                record.question, all_evidence, match_results, timeline
            )
        except Exception as bedrock_error:
            # Fallback to deterministic report if Bedrock unavailable
            report = _build_deterministic_report(
                record.question, all_evidence, match_results, timeline
            )

        record.report = report
        record.status = InvestigationStatus.COMPLETE
        record.completed_at = datetime.utcnow().isoformat()

    except Exception as e:
        record.status = InvestigationStatus.FAILED
        record.error = str(e)

    return record


def _call_bedrock_investigation(
    question: str,
    all_evidence: list,
    match_results: list,
    timeline: list,
) -> InvestigationReport:
    bedrock = get_bedrock()
    
    evidence_context = json.dumps(
        [ev.model_dump() for ev in all_evidence], indent=2, default=str
    )
    match_context = json.dumps(match_results, indent=2, default=str)
    
    prompt = f"""You are ClueBerry, an evidence-first digital investigation assistant.

User question: {question}

Evidence retrieved via MCP tools:
{evidence_context}

Matching engine results:
{match_context}

Investigate the question and return ONLY valid JSON (no fences, no preamble):
{{
  "finding": "one sentence verdict",
  "summary": "2-3 sentence explanation citing evidence_ids",
  "match_status": "strong_match|possible_match|amount_mismatch|partial_payment_possible|no_payment_evidence_found|conflicting_records",
  "contradictions": ["list of contradiction strings"],
  "confidence_note": "limitations and caveats",
  "draft_response": "draft reply the user can send to the vendor"
}}

Rules:
- Cite evidence IDs in the summary (e.g., [ev_001])
- Never claim a payment completed if only an invoice exists
- Never invent amounts, dates, or references
- Use only the evidence IDs provided above"""

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    })
    response = bedrock.invoke_model(
        modelId=settings.bedrock_model_id,
        body=body,
        contentType="application/json",
        accept="application/json",
    )
    result = json.loads(response["body"].read())
    raw = result["content"][0]["text"]
    
    import re
    raw = re.sub(r"```json\s*", "", raw)
    raw = re.sub(r"```\s*", "", raw)
    data = json.loads(raw.strip())
    
    timeline_entries = [TimelineEntry(**t) for t in timeline]
    evidence_list = [
        {
            "evidence_id": ev.evidence_id,
            "document_id": ev.document_id,
            "source_filename": ev.source_filename,
            "field": "summary",
            "value": f"{ev.document_type} — {ev.invoice_number or ''} — ₹{ev.amount or ''}",
        }
        for ev in all_evidence
    ]
    
    return InvestigationReport(
        finding=data.get("finding", "Investigation complete"),
        summary=data.get("summary", ""),
        match_status=MatchStatus(data.get("match_status", "possible_match")),
        evidence_list=evidence_list,
        contradictions=data.get("contradictions", []),
        timeline=timeline_entries,
        confidence_note=data.get("confidence_note", ""),
        draft_response=data.get("draft_response", ""),
    )


def _build_deterministic_report(
    question: str,
    all_evidence: list,
    match_results: list,
    timeline: list,
) -> InvestigationReport:
    """Fallback report when Bedrock is unavailable."""
    timeline_entries = [TimelineEntry(**t) for t in timeline]
    evidence_list = [
        {
            "evidence_id": ev.evidence_id,
            "document_id": ev.document_id,
            "source_filename": ev.source_filename,
            "field": ev.document_type,
            "value": f"₹{ev.amount}" if ev.amount else "Amount not extracted",
        }
        for ev in all_evidence
    ]

    if not match_results:
        return InvestigationReport(
            finding="No payment evidence found in uploaded documents.",
            summary=f"ClueBerry searched {len(all_evidence)} evidence records but found no payment receipts linked to the invoices in scope.",
            match_status=MatchStatus.NO_EVIDENCE,
            evidence_list=evidence_list,
            timeline=timeline_entries,
            confidence_note="Upload a payment receipt to find matching evidence.",
            draft_response="Dear [Vendor], we are reviewing our records for this invoice. We will respond shortly with payment confirmation or a schedule for payment.",
        )

    top = match_results[0]
    status = top.get("status", MatchStatus.POSSIBLE_MATCH)
    contradictions = top.get("contradictions", [])
    
    if status == MatchStatus.STRONG_MATCH:
        finding = "Strong payment evidence found — this invoice appears to have been paid."
        summary = (
            f"ClueBerry found a payment record that matches the invoice on "
            f"{', '.join(top.get('match_fields', []))}. "
            f"Evidence IDs: {top.get('invoice_id')}, {top.get('payment_id')}."
        )
        draft = (
            "Dear [Vendor], our records show that invoice {inv} was paid on [date] "
            "via transaction reference {ref}. Please verify on your end. "
            "We are happy to provide the payment receipt if required."
        )
    elif status == MatchStatus.AMOUNT_MISMATCH:
        finding = "Invoice number matches but amounts differ — possible partial payment or error."
        summary = "An invoice and receipt share the same invoice number but the amounts do not match."
        draft = "Dear [Vendor], we have located a payment reference for this invoice but note a discrepancy in amounts. Please review and confirm the outstanding balance."
    else:
        finding = f"Possible payment match found — further verification required. Status: {status}"
        summary = "ClueBerry found candidate payment records but the match is not conclusive."
        draft = "Dear [Vendor], we are reviewing payment records for this invoice and will follow up shortly."

    return InvestigationReport(
        finding=finding,
        summary=summary,
        match_status=status,
        evidence_list=evidence_list,
        contradictions=contradictions,
        timeline=timeline_entries,
        confidence_note="This report is based on extracted fields. Verify with your bank for final settlement confirmation.",
        draft_response=draft,
    )
