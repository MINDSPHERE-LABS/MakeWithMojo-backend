import os
import uuid
import logging
from typing import Optional
import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger("makewithmojo.r2")

class CloudflareR2Service:
    def __init__(self):
        self.account_id = os.getenv("R2_ACCOUNT_ID", "").strip()
        self.access_key_id = os.getenv("R2_ACCESS_KEY_ID", "").strip()
        self.secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY", "").strip()
        self.bucket_name = os.getenv("R2_BUCKET_NAME", "makewithmojo-images").strip()
        self.public_domain = os.getenv("R2_PUBLIC_DOMAIN", "").strip().rstrip("/")

        self._s3_client = None

    def is_configured(self) -> bool:
        return bool(self.account_id and self.access_key_id and self.secret_access_key and self.public_domain)

    def get_client(self):
        if not self._s3_client and self.is_configured():
            endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"
            logger.info(f"[R2 SERVICE] Initializing S3 client for Cloudflare R2 endpoint: {endpoint_url}")
            self._s3_client = boto3.client(
                service_name='s3',
                endpoint_url=endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name='auto'
            )
        return self._s3_client

    def upload_file(self, file_bytes: bytes, original_filename: str, content_type: str) -> Optional[str]:
        if not self.is_configured():
            logger.warning("[R2 SERVICE] Cloudflare R2 is not fully configured in environment variables.")
            return None

        # Clean file extension
        ext = os.path.splitext(original_filename)[1].lower()
        if not ext or len(ext) > 10:
            ext = ".jpg"

        unique_filename = f"{uuid.uuid4().hex[:12]}{ext}"
        object_key = f"products/{unique_filename}"

        try:
            client = self.get_client()
            client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_bytes,
                ContentType=content_type or 'image/jpeg'
            )
            public_url = f"{self.public_domain}/{object_key}"
            logger.info(f"[R2 SERVICE] Successfully uploaded image to Cloudflare R2: {public_url}")
            return public_url
        except (BotoCoreError, ClientError, Exception) as e:
            logger.error(f"[R2 ERROR] Failed to upload object to Cloudflare R2: {e}")
            return None

r2_service = CloudflareR2Service()
