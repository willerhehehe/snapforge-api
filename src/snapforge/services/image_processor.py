from __future__ import annotations

import io
from PIL import Image


FORMAT_MAP = {
    "png": "PNG",
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "webp": "WEBP",
    "gif": "GIF",
}


def resize_image(
    data: bytes,
    *,
    width: int | None = None,
    height: int | None = None,
    quality: int = 85,
    output_format: str = "png",
) -> bytes:
    img = Image.open(io.BytesIO(data))

    if width and height:
        img = img.resize((width, height), Image.LANCZOS)
    elif width:
        ratio = width / img.width
        img = img.resize((width, int(img.height * ratio)), Image.LANCZOS)
    elif height:
        ratio = height / img.height
        img = img.resize((int(img.width * ratio), height), Image.LANCZOS)

    fmt = FORMAT_MAP.get(output_format.lower(), "PNG")
    if fmt == "JPEG":
        img = img.convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format=fmt, quality=quality, optimize=True)
    return buf.getvalue()


def convert_image(data: bytes, *, output_format: str = "png", quality: int = 85) -> bytes:
    img = Image.open(io.BytesIO(data))
    fmt = FORMAT_MAP.get(output_format.lower(), "PNG")
    if fmt == "JPEG":
        img = img.convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format=fmt, quality=quality, optimize=True)
    return buf.getvalue()


def compress_image(data: bytes, *, quality: int = 60, output_format: str | None = None) -> bytes:
    img = Image.open(io.BytesIO(data))
    detected_fmt = img.format or "PNG"
    fmt = FORMAT_MAP.get(output_format.lower(), detected_fmt) if output_format else detected_fmt

    if fmt == "JPEG":
        img = img.convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format=fmt, quality=quality, optimize=True)
    return buf.getvalue()


def get_image_info(data: bytes) -> dict:
    img = Image.open(io.BytesIO(data))
    return {
        "width": img.width,
        "height": img.height,
        "format": img.format,
        "mode": img.mode,
        "size_bytes": len(data),
    }
