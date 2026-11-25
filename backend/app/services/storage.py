import boto3
import json
from typing import Optional, Any
from app.config import settings

def get_s3():
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )

def get_dynamo():
    return boto3.resource(
        "dynamodb",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )

def get_table():
    dynamo = get_dynamo()
    return dynamo.Table(settings.dynamodb_table)

# ── S3 helpers ──────────────────────────────────────────────

def upload_to_s3(file_bytes: bytes, s3_key: str, content_type: str = "application/octet-stream") -> str:
    s3 = get_s3()
    s3.put_object(
        Bucket=settings.s3_bucket,
        Key=s3_key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return s3_key

def download_from_s3(s3_key: str) -> bytes:
    s3 = get_s3()
    response = s3.get_object(Bucket=settings.s3_bucket, Key=s3_key)
    return response["Body"].read()

# ── DynamoDB helpers ─────────────────────────────────────────

def put_item(pk: str, sk: str, data: dict):
    table = get_table()
    item = {"PK": pk, "SK": sk, **data}
    table.put_item(Item=item)

def get_item(pk: str, sk: str) -> Optional[dict]:
    table = get_table()
    response = table.get_item(Key={"PK": pk, "SK": sk})
    return response.get("Item")

def query_pk(pk: str) -> list:
    table = get_table()
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("PK").eq(pk)
    )
    return response.get("Items", [])

def scan_with_filter(filter_expression, expression_values: dict) -> list:
    table = get_table()
    response = table.scan(
        FilterExpression=filter_expression,
        ExpressionAttributeValues=expression_values,
    )
    return response.get("Items", [])
