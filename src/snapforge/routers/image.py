from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.responses import Response

from snapforge.auth import verify_api_key
from snapforge.services.image_processor import resize_image, convert_image, compress_image, get_image_info

router = APIRouter()


@router.post("/image/resize")
async def image_resize(
    file: UploadFile = File(...),
    width: int | None = Query(None, ge=1, le=8000),
    height: int | None = Query(None, ge=1, le=8000),
    quality: int = Query(85, ge=1, le=100),
    output_format: str = Query("png", pattern="^(png|jpg|jpeg|webp)$"),
    _: str = Depends(verify_api_key),
) -> Response:
    data = await file.read()
    result = resize_image(data, width=width, height=height, quality=quality, output_format=output_format)
    media_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}
    return Response(content=result, media_type=media_map.get(output_format, "image/png"))


@router.post("/image/convert")
async def image_convert(
    file: UploadFile = File(...),
    output_format: str = Query("png", pattern="^(png|jpg|jpeg|webp)$"),
    quality: int = Query(85, ge=1, le=100),
    _: str = Depends(verify_api_key),
) -> Response:
    data = await file.read()
    result = convert_image(data, output_format=output_format, quality=quality)
    media_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}
    return Response(content=result, media_type=media_map.get(output_format, "image/png"))


@router.post("/image/compress")
async def image_compress(
    file: UploadFile = File(...),
    quality: int = Query(60, ge=1, le=100),
    output_format: str | None = Query(None, pattern="^(png|jpg|jpeg|webp)$"),
    _: str = Depends(verify_api_key),
) -> Response:
    data = await file.read()
    result = compress_image(data, quality=quality, output_format=output_format)
    return Response(content=result, media_type="image/png")


@router.post("/image/info")
async def image_info(
    file: UploadFile = File(...),
    _: str = Depends(verify_api_key),
):
    data = await file.read()
    return get_image_info(data)
