from __future__ import annotations

import io

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import (
    SquareModuleDrawer,
    RoundedModuleDrawer,
    CircleModuleDrawer,
)
from qrcode.image.styles.colormasks import SolidFillColorMask
from PIL import Image


DRAWERS = {
    "square": SquareModuleDrawer,
    "rounded": RoundedModuleDrawer,
    "circle": CircleModuleDrawer,
}


def generate_qr(
    data: str,
    *,
    size: int = 400,
    style: str = "square",
    fg_color: str = "#000000",
    bg_color: str = "#ffffff",
    format: str = "png",
    logo_bytes: bytes | None = None,
) -> bytes:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H if logo_bytes else qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    drawer_cls = DRAWERS.get(style, SquareModuleDrawer)

    def _parse_color(hex_str: str) -> tuple[int, int, int]:
        h = hex_str.lstrip("#")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=drawer_cls(),
        color_mask=SolidFillColorMask(
            back_color=_parse_color(bg_color),
            front_color=_parse_color(fg_color),
        ),
    )
    bg = img.convert("RGBA")

    if logo_bytes:
        logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
        logo_size = img.size[0] // 4
        logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
        pos = ((bg.size[0] - logo_size) // 2, (bg.size[1] - logo_size) // 2)
        bg.paste(logo, pos, logo)

    bg = bg.resize((size, size), Image.LANCZOS)

    if format.lower() == "jpg":
        bg = bg.convert("RGB")

    buf = io.BytesIO()
    save_fmt = "JPEG" if format.lower() in ("jpg", "jpeg") else "PNG"
    bg.save(buf, format=save_fmt, quality=95)
    return buf.getvalue()
