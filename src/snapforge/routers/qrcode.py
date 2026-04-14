from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.responses import Response

from snapforge.auth import verify_api_key
from snapforge.services.qr import generate_qr

router = APIRouter()


@router.get("/qr")
async def qr_get(
    data: str = Query(..., description="Data to encode"),
    size: int = Query(400, ge=100, le=2000),
    style: str = Query("square", pattern="^(square|rounded|circle)$"),
    fg_color: str = Query("#000000"),
    bg_color: str = Query("#ffffff"),
    format: str = Query("png", pattern="^(png|jpg)$"),
    _: str = Depends(verify_api_key),
) -> Response:
    img = generate_qr(data, size=size, style=style, fg_color=fg_color, bg_color=bg_color, format=format)
    media = "image/png" if format == "png" else "image/jpeg"
    return Response(content=img, media_type=media)


@router.post("/qr")
async def qr_post(
    data: str = Query(..., description="Data to encode"),
    size: int = Query(400, ge=100, le=2000),
    style: str = Query("square", pattern="^(square|rounded|circle)$"),
    fg_color: str = Query("#000000"),
    bg_color: str = Query("#ffffff"),
    format: str = Query("png", pattern="^(png|jpg)$"),
    logo: UploadFile | None = File(None, description="Logo to embed in center"),
    _: str = Depends(verify_api_key),
) -> Response:
    logo_bytes = await logo.read() if logo else None
    img = generate_qr(data, size=size, style=style, fg_color=fg_color, bg_color=bg_color, format=format, logo_bytes=logo_bytes)
    media = "image/png" if format == "png" else "image/jpeg"
    return Response(content=img, media_type=media)
