import os
import uuid
import logging
from typing import Optional
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

logger = logging.getLogger("makewithmojo.r2")

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("[R2 WARNING] 'boto3' package is not installed. Run 'pip install boto3' to enable Cloudflare R2 uploads.")

class CloudflareR2Service:
    def __init__(self):
        self._s3_client = None

    @property
    def account_id(self) -> str:
        return os.getenv("R2_ACCOUNT_ID", "").strip()

    @property
    def access_key_id(self) -> str:
        return os.getenv("R2_ACCESS_KEY_ID", "").strip()

    @property
    def secret_access_key(self) -> str:
        return os.getenv("R2_SECRET_ACCESS_KEY", "").strip()

    @property
    def bucket_name(self) -> str:
        return os.getenv("R2_BUCKET_NAME", "makewithmojo-images").strip()

    @property
    def public_domain(self) -> str:
        domain = os.getenv("R2_PUBLIC_DOMAIN", "").strip().rstrip("/")
        if domain and not domain.startswith("http://") and not domain.startswith("https://"):
            domain = f"https://{domain}"
        return domain

    def is_configured(self) -> bool:
        load_dotenv()

        if not BOTO3_AVAILABLE:
            logger.warning("[R2 CHECK FAILED] 'boto3' library is missing. Install with: pip install boto3")
            return False

        has_acc = bool(self.account_id)
        has_key = bool(self.access_key_id)
        has_secret = bool(self.secret_access_key)
        has_domain = bool(self.public_domain)

        if not (has_acc and has_key and has_secret and has_domain):
            missing = []
            if not has_acc: missing.append("R2_ACCOUNT_ID")
            if not has_key: missing.append("R2_ACCESS_KEY_ID")
            if not has_secret: missing.append("R2_SECRET_ACCESS_KEY")
            if not has_domain: missing.append("R2_PUBLIC_DOMAIN")
            logger.warning(f"[R2 CHECK FAILED] Missing environment variables in server .env: {', '.join(missing)}")
            return False

        return True

    def get_client(self):
        if not self.is_configured():
            return None

        if not self._s3_client:
            endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"
            logger.info(f"[R2 SERVICE] Initializing S3 client for R2 endpoint: {endpoint_url}")
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
            return None

        ext = os.path.splitext(original_filename)[1].lower()
        if not ext or len(ext) > 10:
            ext = ".jpg"

        unique_filename = f"{uuid.uuid4().hex[:12]}{ext}"
        object_key = f"products/{unique_filename}"

        try:
            client = self.get_client()
            if not client:
                return None

            client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_bytes,
                ContentType=content_type or 'image/jpeg'
            )
            public_url = f"{self.public_domain}/{object_key}"
            logger.info(f"[R2 UPLOAD SUCCESS] Image uploaded to R2 CDN: {public_url}")
            print(f"\n==================================================")
            print(f"[R2 UPLOAD SUCCESS] Image URL: {public_url}")
            print(f"==================================================\n")
            return public_url
        except Exception as e:
            logger.error(f"[R2 UPLOAD ERROR] Failed to upload object to R2: {e}")
            print(f"[R2 UPLOAD ERROR] {e}")
            return None

r2_service = CloudflareR2Service()
