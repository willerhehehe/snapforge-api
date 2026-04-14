from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from snapforge.auth import verify_api_key
from snapforge.services.browser import get_browser_manager

router = APIRouter()


@router.get("/screenshot")
async def take_screenshot(
    url: str = Query(..., description="URL to capture"),
    width: int = Query(1280, ge=320, le=3840),
    height: int = Query(720, ge=240, le=2160),
    full_page: bool = Query(False),
    device_scale_factor: float = Query(1.0, ge=0.5, le=3.0),
    wait_ms: int = Query(0, ge=0, le=10000),
    format: str = Query("png", pattern="^(png|jpg)$"),
    _: str = Depends(verify_api_key),
) -> Response:
    manager = get_browser_manager()
    data = await manager.screenshot(
        url, width=width, height=height, full_page=full_page,
        device_scale_factor=device_scale_factor, wait_ms=wait_ms, format=format,
    )
    media = "image/png" if format == "png" else "image/jpeg"
    return Response(content=data, media_type=media)
