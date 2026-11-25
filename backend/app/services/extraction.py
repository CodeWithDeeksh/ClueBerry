"""
Document text extraction — PyMuPDF for digital PDFs, Textract for scanned,
plain text reader for .txt, mailparser for .eml
"""
import fitz  # PyMuPDF
import email
import json
import re
from typing import Optional
from app.config import settings


def extract_text(file_bytes: bytes, filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        return _extract_pdf(file_bytes, filename)
    elif ext in ("txt",):
        return file_bytes.decode("utf-8", errors="replace")
    elif ext in ("eml", "msg"):
        return _extract_email(file_bytes)
    else:
        return file_bytes.decode("utf-8", errors="replace")


def _extract_pdf(file_bytes: bytes, filename: str) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            pages.append(f"[Page {i+1}]\n{text}")
    full_text = "\n".join(pages)
    # If very little text extracted, it may be a scanned PDF
    if len(full_text.strip()) < 50 and settings.textract_enabled:
        return _extract_with_textract(file_bytes)
    return full_text


def _extract_email(file_bytes: bytes) -> str:
    msg = email.message_from_bytes(file_bytes)
    parts = []
    parts.append(f"From: {msg.get('From', '')}")
    parts.append(f"To: {msg.get('To', '')}")
    parts.append(f"Subject: {msg.get('Subject', '')}")
    parts.append(f"Date: {msg.get('Date', '')}")
    parts.append("")
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    parts.append(payload.decode("utf-8", errors="replace"))
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            parts.append(payload.decode("utf-8", errors="replace"))
    return "\n".join(parts)


def _extract_with_textract(file_bytes: bytes) -> str:
    import boto3
    from app.config import settings
    client = boto3.client(
        "textract",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )
    response = client.detect_document_text(Document={"Bytes": file_bytes})
    lines = [
        block["Text"]
        for block in response.get("Blocks", [])
        if block["BlockType"] == "LINE"
    ]
    return "\n".join(lines)


# ── Bedrock structured extraction ────────────────────────────

def extract_structured_fields(text: str, bedrock_client, model_id: str) -> dict:
    prompt = _load_extraction_prompt()
    full_prompt = f"{prompt}\n\n<document_text>\n{text[:8000]}\n</document_text>"

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": full_prompt}],
    })
    response = bedrock_client.invoke_model(
        modelId=model_id,
        body=body,
        contentType="application/json",
        accept="application/json",
    )
    result_body = json.loads(response["body"].read())
    raw = result_body["content"][0]["text"]
    return _parse_json_safely(raw)


def _load_extraction_prompt() -> str:
    try:
        with open("app/prompts/extraction_prompt.txt") as f:
            return f.read()
    except FileNotFoundError:
        return _default_extraction_prompt()


def _default_extraction_prompt() -> str:
    return """You are the document extraction component of ClueBerry.

Extract structured information from the provided document text.
Return ONLY valid JSON — no markdown fences, no preamble.

JSON structure:
{
  "document_type": "invoice|receipt|reminder|email|unknown",
  "invoice_number": null,
  "vendor_name": null,
  "amount": null,
  "currency": "INR",
  "invoice_date": null,
  "payment_date": null,
  "payment_reference": null,
  "payment_status": null,
  "evidence_items": [
    {"field": "invoice_number", "value": "...", "source_text": "..."}
  ]
}

Rules:
1. Never invent missing information.
2. Use null for unavailable fields.
3. Do not assume an invoice is paid because it has payment instructions.
4. Distinguish invoice_date, due_date, and payment_date.
5. Distinguish requested payment from completed payment.
6. Preserve the exact source text for important fields.
7. Return valid JSON only."""


def _parse_json_safely(raw: str) -> dict:
    # Strip markdown fences if present
    raw = re.sub(r"```json\s*", "", raw)
    raw = re.sub(r"```\s*", "", raw)
    try:
        return json.loads(raw.strip())
    except Exception:
        return {"parse_error": True, "raw": raw[:500]}
