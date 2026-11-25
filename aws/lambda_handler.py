"""
AWS Lambda handler for async document processing.
Triggered by S3 upload events.

This can be deployed independently after the core demo works.
During the hackathon, the same logic runs synchronously in FastAPI.
"""
import json
import boto3
import os
import sys

sys.path.insert(0, "/opt/python")

from app.config import settings
from app.services import extraction, evidence_store, storage as storage_svc
from app.models.document import DocumentStatus
from app.models.evidence import Evidence


def handler(event, context):
    """
    S3 trigger: extracts text, calls Bedrock, saves evidence to DynamoDB.
    """
    for record in event.get("Records", []):
        s3_key = record["s3"]["object"]["key"]
        bucket = record["s3"]["bucket"]["name"]

        # Derive document_id from key (format: documents/{doc_id}/{filename})
        parts = s3_key.split("/")
        if len(parts) < 3:
            print(f"Unexpected S3 key format: {s3_key}")
            continue

        document_id = parts[1]
        filename = parts[2]

        try:
            # Download file
            s3 = boto3.client("s3")
            response = s3.get_object(Bucket=bucket, Key=s3_key)
            file_bytes = response["Body"].read()

            # Extract text
            text = extraction.extract_text(file_bytes, filename)

            # Bedrock structured extraction
            bedrock = boto3.client("bedrock-runtime", region_name=settings.aws_region)
            fields = extraction.extract_structured_fields(text, bedrock, settings.bedrock_model_id)

            # Save evidence
            ev = Evidence(
                document_id=document_id,
                source_filename=filename,
                document_type=fields.get("document_type", "unknown"),
                invoice_number=fields.get("invoice_number"),
                vendor_name=fields.get("vendor_name"),
                amount=fields.get("amount"),
                currency=fields.get("currency", "INR"),
                invoice_date=fields.get("invoice_date"),
                payment_date=fields.get("payment_date"),
                payment_reference=fields.get("payment_reference"),
                payment_status=fields.get("payment_status"),
            )
            evidence_store.save_evidence(ev)
            evidence_store.update_document_status(document_id, DocumentStatus.READY)

            print(f"Processed {document_id}: {filename} → {ev.document_type}, ₹{ev.amount}")

        except Exception as e:
            print(f"Error processing {document_id}: {e}")
            evidence_store.update_document_status(document_id, DocumentStatus.FAILED, str(e))

    return {"statusCode": 200, "body": "OK"}
