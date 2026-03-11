import io

from PIL import Image
from pillow_heif import register_heif_opener

# Register HEIF opener to support .heic files
register_heif_opener()

_OUTPUT_FORMAT = "AVIF"
_OUTPUT_CONTENT_TYPE = "image/avif"
_OUTPUT_EXT = ".avif"


def process_image_variants(image_bytes: bytes, file_name: str) -> dict[str, dict[str, bytes | str]]:
    """
    Processes an image once and returns both full and thumbnail variants.
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Ensure compatible mode for AVIF
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in (img.mode or "") else "RGB")

    base_name = file_name.rsplit(".", 1)[0] if "." in file_name else file_name

    # 1. Full resolution variant
    full_io = io.BytesIO()
    img.save(full_io, format=_OUTPUT_FORMAT, quality=70)

    # 2. Thumbnail variant
    thumb_img = img.copy()
    thumb_img.thumbnail((400, 400))
    thumb_io = io.BytesIO()
    thumb_img.save(thumb_io, format=_OUTPUT_FORMAT, quality=60)

    return {
        "full": {
            "content": full_io.getvalue(),
            "name": f"{base_name}{_OUTPUT_EXT}",
            "content_type": _OUTPUT_CONTENT_TYPE,
        },
        "thumb": {
            "content": thumb_io.getvalue(),
            "name": f"thumb_{base_name}{_OUTPUT_EXT}",
            "content_type": _OUTPUT_CONTENT_TYPE,
        },
    }


def convert_to_avif(
    image_bytes: bytes, file_name: str, quality: int = 70
) -> tuple[bytes, str, str]:
    """
    Converts any image to AVIF format for optimal compression.
    Returns: (converted_bytes, new_file_name, content_type)
    """
    img = Image.open(io.BytesIO(image_bytes))

    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in (img.mode or "") else "RGB")

    output = io.BytesIO()
    img.save(output, format=_OUTPUT_FORMAT, quality=quality)

    base = file_name.rsplit(".", 1)[0] if "." in file_name else file_name
    new_name = f"{base}{_OUTPUT_EXT}"
    return output.getvalue(), new_name, _OUTPUT_CONTENT_TYPE


def create_thumbnail(
    image_bytes: bytes, size: tuple[int, int] = (400, 400), quality: int = 60
) -> bytes:
    """
    Creates an AVIF thumbnail from image bytes.
    """
    img = Image.open(io.BytesIO(image_bytes))

    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    img.thumbnail(size)

    output = io.BytesIO()
    img.save(output, format=_OUTPUT_FORMAT, quality=quality)
    return output.getvalue()
