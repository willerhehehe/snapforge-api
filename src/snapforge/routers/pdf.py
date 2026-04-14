from fastapi import APIRouter, Depends, Body, Query
from fastapi.responses import Response

from snapforge.auth import verify_api_key
from snapforge.services.browser import get_browser_manager

router = APIRouter()


@router.post("/pdf/from-html")
async def pdf_from_html(
    html: str = Body(..., media_type="text/html"),
    width: str = Query("210mm", description="Page width"),
    height: str = Query("297mm", description="Page height"),
    _: str = Depends(verify_api_key),
) -> Response:
    manager = get_browser_manager()
    data = await manager.html_to_pdf(html, width=width, height=height)
    return Response(content=data, media_type="application/pdf")
