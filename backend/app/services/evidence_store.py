"""
Save and retrieve evidence records from DynamoDB.
"""
from typing import Optional, List
from app.models.evidence import Evidence
from app.models.document import DocumentMeta, DocumentStatus
from app.services import storage
import json


def save_document_meta(doc: DocumentMeta):
    storage.put_item(
        pk=f"DOC#{doc.document_id}",
        sk="META",
        data=doc.model_dump(),
    )


def get_document_meta(document_id: str) -> Optional[DocumentMeta]:
    item = storage.get_item(f"DOC#{document_id}", "META")
    if not item:
        return None
    return DocumentMeta(**{k: v for k, v in item.items() if k not in ("PK", "SK")})


def list_documents() -> List[DocumentMeta]:
    table = storage.get_table()
    response = table.scan(
        FilterExpression="begins_with(PK, :prefix) AND SK = :sk",
        ExpressionAttributeValues={":prefix": "DOC#", ":sk": "META"},
    )
    items = response.get("Items", [])
    return [DocumentMeta(**{k: v for k, v in item.items() if k not in ("PK", "SK")}) for item in items]


def save_evidence(ev: Evidence):
    storage.put_item(
        pk=f"DOC#{ev.document_id}",
        sk=f"EVIDENCE#{ev.evidence_id}",
        data=ev.model_dump(),
    )


def get_evidence_for_document(document_id: str) -> List[Evidence]:
    items = storage.query_pk(f"DOC#{document_id}")
    results = []
    for item in items:
        if item.get("SK", "").startswith("EVIDENCE#"):
            results.append(Evidence(**{k: v for k, v in item.items() if k not in ("PK", "SK")}))
    return results


def search_evidence(
    query: str = "",
    document_type: Optional[str] = None,
    invoice_number: Optional[str] = None,
    document_ids: Optional[List[str]] = None,
) -> List[Evidence]:
    """
    Search evidence records. For the MVP, scan all evidence records
    and filter by invoice_number or document_type.
    In production this would use GSIs or a search index.
    """
    table = storage.get_table()
    
    # Collect all evidence items
    response = table.scan(
        FilterExpression="begins_with(SK, :sk_prefix)",
        ExpressionAttributeValues={":sk_prefix": "EVIDENCE#"},
    )
    items = response.get("Items", [])
    
    results = []
    for item in items:
        try:
            ev = Evidence(**{k: v for k, v in item.items() if k not in ("PK", "SK")})
        except Exception:
            continue
        
        # Filter by document_ids scope if provided
        if document_ids and ev.document_id not in document_ids:
            continue
        
        # Filter by document type
        if document_type and ev.document_type != document_type:
            continue
        
        # Filter by invoice number
        if invoice_number and ev.invoice_number:
            if invoice_number.lower() not in ev.invoice_number.lower():
                continue
        elif invoice_number and not ev.invoice_number:
            continue
        
        results.append(ev)
    
    return results


def update_document_status(document_id: str, status: DocumentStatus, error: str = None):
    table = storage.get_table()
    update_expr = "SET #s = :status"
    expr_names = {"#s": "status"}
    expr_values = {":status": status.value}
    if error:
        update_expr += ", #e = :error"
        expr_names["#e"] = "error"
        expr_values[":error"] = error
    table.update_item(
        Key={"PK": f"DOC#{document_id}", "SK": "META"},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
    )
