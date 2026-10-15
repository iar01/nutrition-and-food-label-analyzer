import io

from fastapi import UploadFile
from PIL import Image, ImageOps

from labellens.api.errors import ApiError

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
Image.MAX_IMAGE_PIXELS = 25_000_000  # refuse decompression bombs


async def read_limited(upload: UploadFile, max_bytes: int) -> bytes:
    if upload.content_type not in ALLOWED_MIME:
        raise ApiError(415, "unsupported_media_type", "Upload a JPEG, PNG or WebP image.")
    chunks: list[bytes] = []
    total = 0
    while chunk := await upload.read(64 * 1024):
        total += len(chunk)
        if total > max_bytes:
            raise ApiError(
                413, "file_too_large", f"The image must be at most {max_bytes // 1_000_000} MB."
            )
        chunks.append(chunk)
    return b"".join(chunks)


def clean_image(raw: bytes) -> Image.Image:
    """Validate the real content and return a metadata-free RGB copy."""
    try:
        with Image.open(io.BytesIO(raw)) as probe:
            image_format = probe.format
            probe.verify()  # verify() invalidates the object, so we reopen below
        if image_format not in ALLOWED_FORMATS:
            raise ValueError(f"unexpected format {image_format}")
        with Image.open(io.BytesIO(raw)) as opened:
            rotated = ImageOps.exif_transpose(opened)  # apply the camera orientation
            rgb = rotated.convert("RGB")
            clean = Image.new("RGB", rgb.size)  # a fresh image carries no metadata at all
            clean.paste(rgb)
            return clean
    except ApiError:
        raise
    except Exception as exc:  # corrupt files, truncated files, decompression bombs...
        raise ApiError(415, "invalid_image", "The file is not a valid image.") from exc
