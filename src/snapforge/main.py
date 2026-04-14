from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from snapforge.routers import screenshot, qrcode, og_image, image, pdf

TEMPLATES_DIR = Path(__file__).parent / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    from snapforge.services.browser import get_browser_manager
    manager = get_browser_manager()
    await manager.start()
    yield
    await manager.stop()


def create_app() -> FastAPI:
    app = FastAPI(
        title="SnapForge API",
        version="0.1.0",
        description="File processing micro-SaaS API — screenshots, QR codes, OG images, image processing, PDF generation",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(screenshot.router, prefix="/api/v1", tags=["screenshot"])
    app.include_router(qrcode.router, prefix="/api/v1", tags=["qrcode"])
    app.include_router(og_image.router, prefix="/api/v1", tags=["og-image"])
    app.include_router(image.router, prefix="/api/v1", tags=["image"])
    app.include_router(pdf.router, prefix="/api/v1", tags=["pdf"])

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def landing():
        return (TEMPLATES_DIR / "landing.html").read_text()

    @app.get("/health")
    def health():
        return {"status": "ok", "version": "0.1.0"}

    return app


app = create_app()
