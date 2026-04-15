from __future__ import annotations

import base64
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from snapforge.services.browser import get_browser_manager
from snapforge.services.image_processor import resize_image, convert_image, compress_image, get_image_info
from snapforge.services.og import generate_og_image
from snapforge.services.qr import generate_qr


@asynccontextmanager
async def lifespan(server):
    manager = get_browser_manager()
    await manager.start()
    yield
    await manager.stop()


mcp = FastMCP(
    name="SnapForge",
    instructions="File processing tools: screenshots, QR codes, OG images, image processing, and PDF generation. Binary data is base64-encoded.",
    lifespan=lifespan,
)


@mcp.tool()
async def take_screenshot(
    url: str,
    width: int = 1280,
    height: int = 720,
    full_page: bool = False,
    device_scale_factor: float = 1.0,
    wait_ms: int = 0,
    output_path: str = "screenshot.png",
) -> str:
    """Capture a screenshot of a webpage. Saves to output_path and returns the file path."""
    manager = get_browser_manager()
    data = await manager.screenshot(
        url, width=width, height=height, full_page=full_page,
        device_scale_factor=device_scale_factor, wait_ms=wait_ms, format="png",
    )
    with open(output_path, "wb") as f:
        f.write(data)
    return f"Screenshot saved to {output_path} ({len(data)} bytes, {width}x{height})"


@mcp.tool()
async def html_to_pdf(
    html: str,
    output_path: str = "output.pdf",
    width: str = "210mm",
    height: str = "297mm",
) -> str:
    """Convert HTML content to a PDF file. Saves to output_path and returns the file path."""
    manager = get_browser_manager()
    data = await manager.html_to_pdf(html, width=width, height=height)
    with open(output_path, "wb") as f:
        f.write(data)
    return f"PDF saved to {output_path} ({len(data)} bytes)"


@mcp.tool()
def generate_qr_code(
    data: str,
    output_path: str = "qr.png",
    size: int = 400,
    style: str = "square",
    fg_color: str = "#000000",
    bg_color: str = "#ffffff",
) -> str:
    """Generate a QR code image. Style can be 'square', 'rounded', or 'circle'. Saves to output_path."""
    result = generate_qr(data, size=size, style=style, fg_color=fg_color, bg_color=bg_color)
    with open(output_path, "wb") as f:
        f.write(result)
    return f"QR code saved to {output_path} ({len(result)} bytes, {size}x{size}, style={style})"


@mcp.tool()
def generate_social_image(
    title: str,
    output_path: str = "og.png",
    subtitle: str = "",
    bg_color: str = "#1e293b",
    text_color: str = "#ffffff",
    accent_color: str = "#3b82f6",
    width: int = 1200,
    height: int = 630,
) -> str:
    """Generate an Open Graph social sharing image with title and subtitle. Saves to output_path."""
    result = generate_og_image(
        title, subtitle=subtitle, bg_color=bg_color, text_color=text_color,
        accent_color=accent_color, width=width, height=height,
    )
    with open(output_path, "wb") as f:
        f.write(result)
    return f"OG image saved to {output_path} ({len(result)} bytes, {width}x{height})"


@mcp.tool()
def resize_image_tool(
    input_path: str,
    output_path: str = "resized.png",
    width: int | None = None,
    height: int | None = None,
    quality: int = 85,
    output_format: str = "png",
) -> str:
    """Resize an image file. Specify width, height, or both. Maintains aspect ratio if only one dimension given."""
    with open(input_path, "rb") as f:
        data = f.read()
    result = resize_image(data, width=width, height=height, quality=quality, output_format=output_format)
    with open(output_path, "wb") as f:
        f.write(result)
    return f"Resized image saved to {output_path} ({len(result)} bytes)"


@mcp.tool()
def convert_image_tool(
    input_path: str,
    output_format: str = "webp",
    output_path: str | None = None,
    quality: int = 85,
) -> str:
    """Convert an image to a different format (png, jpg, webp). Saves to output_path."""
    if output_path is None:
        output_path = f"converted.{output_format}"
    with open(input_path, "rb") as f:
        data = f.read()
    result = convert_image(data, output_format=output_format, quality=quality)
    with open(output_path, "wb") as f:
        f.write(result)
    return f"Converted image saved to {output_path} ({len(result)} bytes, format={output_format})"


@mcp.tool()
def compress_image_tool(
    input_path: str,
    output_path: str = "compressed.png",
    quality: int = 60,
    output_format: str | None = None,
) -> str:
    """Compress an image to reduce file size. Lower quality = smaller file."""
    with open(input_path, "rb") as f:
        data = f.read()
    result = compress_image(data, quality=quality, output_format=output_format)
    with open(output_path, "wb") as f:
        f.write(result)
    original_size = len(data)
    new_size = len(result)
    reduction = round((1 - new_size / original_size) * 100, 1)
    return f"Compressed image saved to {output_path} ({new_size} bytes, {reduction}% reduction)"


@mcp.tool()
def get_image_info_tool(input_path: str) -> dict:
    """Get metadata about an image file: dimensions, format, color mode, and file size."""
    with open(input_path, "rb") as f:
        data = f.read()
    return get_image_info(data)


if __name__ == "__main__":
    mcp.run(transport="stdio")
