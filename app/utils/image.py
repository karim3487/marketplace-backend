import io

from PIL import Image


def create_thumbnail(image_bytes: bytes, size: tuple[int, int] = (200, 200)) -> bytes:
    """
    Creates a thumbnail of an image from bytes.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        # Provide more context for PIL identification errors
        print(f"Failed to identify image. First 32 bytes: {image_bytes[:32].hex()}")
        raise e

    # Convert to RGB if necessary (e.g. for RGBA/PNG to JPEG)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    img.thumbnail(size)

    output = io.BytesIO()
    img.save(output, format="JPEG", quality=85)
    return output.getvalue()
