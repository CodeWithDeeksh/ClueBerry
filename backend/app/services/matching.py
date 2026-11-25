"""
Deterministic invoice-payment matching engine.
No LLM is used here — only structured field comparisons.
"""
from typing import List, Optional, Dict, Any
from app.models.evidence import Evidence
from app.models.investigation import MatchStatus


def normalize_string(s: Optional[str]) -> str:
    if not s:
        return ""
    return s.lower().strip().replace(" ", "").replace("-", "").replace("_", "")


def amounts_match(a: Optional[float], b: Optional[float], tolerance: float = 0.01) -> bool:
    if a is None or b is None:
        return False
    return abs(a - b) <= tolerance


def match_invoice_to_payment(invoice: Evidence, payment: Evidence) -> Dict[str, Any]:
    result = {
        "invoice_id": invoice.evidence_id,
        "payment_id": payment.evidence_id,
        "invoice_document_id": invoice.document_id,
        "payment_document_id": payment.document_id,
        "invoice_number_match": False,
        "amount_match": False,
        "vendor_match": False,
        "payment_reference_match": False,
        "status": MatchStatus.NO_EVIDENCE,
        "contradictions": [],
        "match_fields": [],
    }

    # Invoice number match (strong identifier)
    if invoice.invoice_number and payment.invoice_number:
        if normalize_string(invoice.invoice_number) == normalize_string(payment.invoice_number):
            result["invoice_number_match"] = True
            result["match_fields"].append("invoice_number")
        else:
            result["contradictions"].append(
                f"Invoice numbers differ: invoice has '{invoice.invoice_number}', "
                f"receipt references '{payment.invoice_number}'"
            )

    # Amount match (required supporting field)
    if invoice.amount is not None and payment.amount is not None:
        if amounts_match(invoice.amount, payment.amount):
            result["amount_match"] = True
            result["match_fields"].append("amount")
        else:
            diff = abs((invoice.amount or 0) - (payment.amount or 0))
            result["contradictions"].append(
                f"Amount mismatch: invoice ₹{invoice.amount}, receipt ₹{payment.amount} "
                f"(difference: ₹{diff:.2f})"
            )

    # Vendor name match (supporting)
    if invoice.vendor_name and payment.vendor_name:
        if normalize_string(invoice.vendor_name) == normalize_string(payment.vendor_name):
            result["vendor_match"] = True
            result["match_fields"].append("vendor_name")

    # Payment reference (strong if present)
    if invoice.payment_reference and payment.payment_reference:
        if normalize_string(invoice.payment_reference) == normalize_string(payment.payment_reference):
            result["payment_reference_match"] = True
            result["match_fields"].append("payment_reference")

    # Determine overall status
    result["status"] = _determine_status(result)
    return result


def _determine_status(result: Dict[str, Any]) -> MatchStatus:
    strong_matches = sum([
        result["invoice_number_match"],
        result["payment_reference_match"],
    ])
    support_matches = sum([
        result["amount_match"],
        result["vendor_match"],
    ])
    contradictions = result["contradictions"]

    if strong_matches >= 1 and result["amount_match"] and not contradictions:
        return MatchStatus.STRONG_MATCH
    elif strong_matches >= 1 and not result["amount_match"] and contradictions:
        # Invoice number matches but amount differs
        return MatchStatus.AMOUNT_MISMATCH
    elif strong_matches >= 1 and support_matches >= 1:
        return MatchStatus.POSSIBLE_MATCH
    elif contradictions and strong_matches == 0:
        return MatchStatus.CONFLICTING
    elif strong_matches == 0 and support_matches == 0:
        return MatchStatus.NO_EVIDENCE
    else:
        return MatchStatus.POSSIBLE_MATCH


def find_payment_matches(
    invoice: Evidence,
    all_evidence: List[Evidence],
) -> List[Dict[str, Any]]:
    """
    Find all candidate payment records for an invoice
    and return match results.
    """
    payment_types = {"receipt", "payment", "payment_receipt"}
    candidates = [
        ev for ev in all_evidence
        if ev.evidence_id != invoice.evidence_id
        and (ev.document_type or "").lower() in payment_types
    ]
    return [match_invoice_to_payment(invoice, payment) for payment in candidates]


def build_timeline(all_evidence: List[Evidence]) -> List[Dict[str, Any]]:
    """
    Build a chronological timeline from evidence dates.
    """
    events = []
    for ev in all_evidence:
        if ev.invoice_date:
            events.append({
                "date": ev.invoice_date,
                "event": f"Invoice {ev.invoice_number or ''} issued for {ev.currency} {ev.amount}",
                "document_id": ev.document_id,
                "source_filename": ev.source_filename,
                "evidence_id": ev.evidence_id,
            })
        if ev.payment_date:
            events.append({
                "date": ev.payment_date,
                "event": f"Payment of {ev.currency} {ev.amount} recorded "
                         f"(ref: {ev.payment_reference or 'N/A'})",
                "document_id": ev.document_id,
                "source_filename": ev.source_filename,
                "evidence_id": ev.evidence_id,
            })

    # Sort by date string (ISO format sorts correctly)
    events.sort(key=lambda x: x.get("date") or "")
    return events
