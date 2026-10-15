import io
from uuid import uuid4
from PIL import Image, UnidentifiedImageError
import boto3
from oriade.shared.config import settings
from oriade.shared.errors import Problem


def upload(file):
    config = settings()
    if not config.s3_bucket or not config.s3_public_url:
        raise Problem("Image storage is not configured. Add object-storage settings before uploading.", 503)
    data = file.file.read(5 * 1024 * 1024 + 1)
    if len(data) > 5 * 1024 * 1024:
        raise Problem("Images must be under 5 MB.", 413)
    try:
        Image.MAX_IMAGE_PIXELS = 20_000_000
        image = Image.open(io.BytesIO(data))
        image.load()
        image = image.convert("RGB")
        image.thumbnail((1600, 1600))
        buffer = io.BytesIO()
        image.save(buffer, format="WEBP", quality=85)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise Problem("Upload a valid JPEG, PNG, or WebP image.")
    key = f"menu/{uuid4()}.webp"
    boto3.client("s3", endpoint_url=config.s3_endpoint_url or None).put_object(
        Bucket=config.s3_bucket,
        Key=key,
        Body=buffer.getvalue(),
        ContentType="image/webp",
        CacheControl="public,max-age=31536000,immutable",
    )
    return {"url": f"{config.s3_public_url.rstrip('/')}/{key}"}
