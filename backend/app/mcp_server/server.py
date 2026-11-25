"""
ClueBerry MCP Server
Exposes three evidence tools to the investigation reasoning loop.
"""
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from typing import Optional, List
import json

from app.services import evidence_store, matching as matching_svc
from app.models.evidence import Evidence

server = Server("clueberry-evidence-server")

# Shared scope set by the investigation service before tool calls
_investigation_scope: List[str] = []  # document_ids in scope


def set_scope(document_ids: List[str]):
    global _investigation_scope
    _investigation_scope = document_ids


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_evidence",
            description=(
                "Search extracted evidence records. Use this first to find "
                "relevant invoices, receipts, and reminders."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language search query"},
                    "document_type": {
                        "type": "string",
                        "enum": ["invoice", "receipt", "reminder", "email"],
                        "description": "Filter by document type",
                    },
                    "invoice_number": {
                        "type": "string",
                        "description": "Filter by invoice number",
                    },
                },
            },
        ),
        Tool(
            name="read_source",
            description=(
                "Retrieve original source text and extracted fields "
                "for a specific document or evidence record."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "Document ID"},
                    "evidence_id": {
                        "type": "string",
                        "description": "Specific evidence record ID (optional)",
                    },
                },
                "required": ["document_id"],
            },
        ),
        Tool(
            name="find_payment_match",
            description=(
                "Find payment records that match a given invoice. "
                "Returns match status and any contradictions detected."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_number": {"type": "string"},
                    "vendor_name": {"type": "string"},
                    "amount": {"type": "number"},
                },
                "required": ["invoice_number"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search_evidence":
        return await _search_evidence(**arguments)
    elif name == "read_source":
        return await _read_source(**arguments)
    elif name == "find_payment_match":
        return await _find_payment_match(**arguments)
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def _search_evidence(
    query: str = "",
    document_type: Optional[str] = None,
    invoice_number: Optional[str] = None,
) -> list:
    results = evidence_store.search_evidence(
        query=query,
        document_type=document_type,
        invoice_number=invoice_number,
        document_ids=_investigation_scope if _investigation_scope else None,
    )
    if not results:
        return [TextContent(type="text", text="No evidence records found matching the query.")]
    
    summaries = []
    for ev in results:
        summaries.append({
            "evidence_id": ev.evidence_id,
            "document_id": ev.document_id,
            "source_filename": ev.source_filename,
            "document_type": ev.document_type,
            "invoice_number": ev.invoice_number,
            "vendor_name": ev.vendor_name,
            "amount": ev.amount,
            "currency": ev.currency,
            "invoice_date": ev.invoice_date,
            "payment_date": ev.payment_date,
            "payment_reference": ev.payment_reference,
        })
    return [TextContent(type="text", text=json.dumps(summaries, indent=2))]


async def _read_source(
    document_id: str,
    evidence_id: Optional[str] = None,
) -> list:
    if evidence_id:
        all_ev = evidence_store.get_evidence_for_document(document_id)
        for ev in all_ev:
            if ev.evidence_id == evidence_id:
                return [TextContent(type="text", text=json.dumps({
                    "evidence_id": ev.evidence_id,
                    "document_id": ev.document_id,
                    "source_filename": ev.source_filename,
                    "source_location": ev.source_location,
                    "evidence_items": [item.model_dump() for item in ev.evidence_items],
                }, indent=2))]
        return [TextContent(type="text", text=f"Evidence ID {evidence_id} not found.")]
    else:
        doc = evidence_store.get_document_meta(document_id)
        if not doc:
            return [TextContent(type="text", text=f"Document {document_id} not found.")]
        ev_list = evidence_store.get_evidence_for_document(document_id)
        return [TextContent(type="text", text=json.dumps({
            "document_id": document_id,
            "filename": doc.filename,
            "document_type": doc.document_type,
            "status": doc.status,
            "evidence_count": len(ev_list),
            "evidence_summary": [
                {"evidence_id": e.evidence_id, "document_type": e.document_type,
                 "invoice_number": e.invoice_number, "amount": e.amount}
                for e in ev_list
            ],
        }, indent=2))]


async def _find_payment_match(
    invoice_number: str,
    vendor_name: Optional[str] = None,
    amount: Optional[float] = None,
) -> list:
    all_evidence = evidence_store.search_evidence(
        document_ids=_investigation_scope if _investigation_scope else None,
    )
    
    # Find the invoice
    invoices = [
        ev for ev in all_evidence
        if ev.invoice_number and invoice_number.lower() in ev.invoice_number.lower()
        and (ev.document_type or "").lower() == "invoice"
    ]
    
    if not invoices:
        return [TextContent(type="text", text=f"No invoice found with number '{invoice_number}' in scope.")]
    
    invoice = invoices[0]
    matches = matching_svc.find_payment_matches(invoice, all_evidence)
    
    if not matches:
        return [TextContent(type="text", text=json.dumps({
            "invoice_evidence_id": invoice.evidence_id,
            "invoice_number": invoice_number,
            "result": "no_payment_evidence_found",
            "message": "No payment receipts found in the uploaded documents.",
        }, indent=2))]
    
    return [TextContent(type="text", text=json.dumps({
        "invoice_evidence_id": invoice.evidence_id,
        "invoice_number": invoice_number,
        "matches_found": len(matches),
        "match_results": matches,
    }, indent=2, default=str))]


async def run_server():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())
