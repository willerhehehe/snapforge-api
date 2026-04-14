from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from snapforge.auth import verify_api_key
from snapforge.services.og import generate_og_image

router = APIRouter()


@router.get("/og-image")
async def og_image(
    title: str = Query(..., description="Main title text"),
    subtitle: str = Query("", description="Subtitle text"),
    bg_color: str = Query("#1e293b"),
    text_color: str = Query("#ffffff"),
    accent_color: str = Query("#3b82f6"),
    width: int = Query(1200, ge=600, le=2400),
    height: int = Query(630, ge=315, le=1260),
    format: str = Query("png", pattern="^(png|jpg)$"),
    _: str = Depends(verify_api_key),
) -> Response:
    img = generate_og_image(
        title, subtitle=subtitle, bg_color=bg_color, text_color=text_color,
        accent_color=accent_color, width=width, height=height, format=format,
    )
    media = "image/png" if format == "png" else "image/jpeg"
    return Response(content=img, media_type=media)
