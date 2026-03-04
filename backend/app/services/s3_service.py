"""S3 / MinIO file storage service."""

from __future__ import annotations

import logging

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = None


def get_s3_client():
    """Return a reusable boto3 S3 client configured from settings."""
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name="us-east-1",
        )
    return _client


def ensure_bucket_exists(client=None) -> None:
    """Create the configured S3 bucket if it does not already exist."""
    client = client or get_s3_client()
    try:
        client.head_bucket(Bucket=settings.S3_BUCKET)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("404", "NoSuchBucket"):
            client.create_bucket(Bucket=settings.S3_BUCKET)
            logger.info("Created S3 bucket: %s", settings.S3_BUCKET)
        else:
            raise


def upload_file(
    file_content: bytes,
    key: str,
    content_type: str = "application/pdf",
    client=None,
) -> str:
    """Upload file bytes to S3 and return the object key."""
    client = client or get_s3_client()
    ensure_bucket_exists(client)
    client.put_object(
        Bucket=settings.S3_BUCKET,
        Key=key,
        Body=file_content,
        ContentType=content_type,
    )
    logger.info("Uploaded %s (%d bytes)", key, len(file_content))
    return key


def download_file(key: str, client=None) -> bytes:
    """Download a file from S3 by key."""
    client = client or get_s3_client()
    response = client.get_object(Bucket=settings.S3_BUCKET, Key=key)
    return response["Body"].read()


def delete_file(key: str, client=None) -> None:
    """Delete a file from S3 by key."""
    client = client or get_s3_client()
    client.delete_object(Bucket=settings.S3_BUCKET, Key=key)
    logger.info("Deleted %s", key)


def generate_presigned_url(
    key: str,
    expires_in: int = 3600,
    client=None,
) -> str:
    """Generate a presigned URL for temporary file access."""
    client = client or get_s3_client()
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key},
        ExpiresIn=expires_in,
    )
    return url
