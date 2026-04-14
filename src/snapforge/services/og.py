from __future__ import annotations

import io
from PIL import Image, ImageDraw, ImageFont


def generate_og_image(
    title: str,
    *,
    subtitle: str = "",
    bg_color: str = "#1e293b",
    text_color: str = "#ffffff",
    accent_color: str = "#3b82f6",
    width: int = 1200,
    height: int = 630,
    format: str = "png",
) -> bytes:
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, height - 6, width, height], fill=accent_color)

    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        sub_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except (OSError, IOError):
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
            sub_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        except (OSError, IOError):
            title_font = ImageFont.load_default()
            sub_font = ImageFont.load_default()

    margin = 80
    max_text_width = width - margin * 2

    lines = _wrap_text(draw, title, title_font, max_text_width)
    y = height // 2 - len(lines) * 56 // 2 - (20 if subtitle else 0)

    for line in lines[:3]:
        draw.text((margin, y), line, fill=text_color, font=title_font)
        y += 56

    if subtitle:
        y += 16
        draw.text((margin, y), subtitle[:100], fill="#94a3b8", font=sub_font)

    draw.rectangle([margin, height // 2 - len(lines) * 56 // 2 - 40, margin + 4, y - 8], fill=accent_color)

    buf = io.BytesIO()
    save_fmt = "JPEG" if format.lower() in ("jpg", "jpeg") else "PNG"
    if save_fmt == "JPEG":
        img = img.convert("RGB")
    img.save(buf, format=save_fmt, quality=95)
    return buf.getvalue()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
