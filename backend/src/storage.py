from minio import Minio
from minio.error import S3Error
from .config import settings
import io

minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE
)

BUCKET_NAME = "bidding-projects"

def ensure_bucket_exists():
    found = minio_client.bucket_exists(BUCKET_NAME)
    if not found:
        minio_client.make_bucket(BUCKET_NAME)

def upload_file(project_id: int, filename: str, data: bytes):
    ensure_bucket_exists()
    object_name = f"project-{project_id}/{filename}"
    minio_client.put_object(
        BUCKET_NAME,
        object_name,
        data=io.BytesIO(data),
        length=len(data)
    )
    return object_name

def get_file_url(object_name: str):
    return minio_client.presigned_get_object(BUCKET_NAME, object_name)
