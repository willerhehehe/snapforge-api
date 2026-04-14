from __future__ import annotations

import asyncio
from playwright.async_api import async_playwright, Browser, Playwright


class BrowserManager:
    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def screenshot(
        self,
        url: str,
        *,
        width: int = 1280,
        height: int = 720,
        full_page: bool = False,
        device_scale_factor: float = 1.0,
        wait_ms: int = 0,
        format: str = "png",
    ) -> bytes:
        async with self._lock:
            if not self._browser:
                raise RuntimeError("Browser not started")
            page = await self._browser.new_page(
                viewport={"width": width, "height": height},
                device_scale_factor=device_scale_factor,
            )
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                if wait_ms > 0:
                    await page.wait_for_timeout(wait_ms)
                return await page.screenshot(full_page=full_page, type=format)
            finally:
                await page.close()

    async def html_to_pdf(self, html: str, *, width: str = "210mm", height: str = "297mm") -> bytes:
        async with self._lock:
            if not self._browser:
                raise RuntimeError("Browser not started")
            page = await self._browser.new_page()
            try:
                await page.set_content(html, wait_until="networkidle")
                return await page.pdf(width=width, height=height, print_background=True)
            finally:
                await page.close()


_manager: BrowserManager | None = None


def get_browser_manager() -> BrowserManager:
    global _manager
    if _manager is None:
        _manager = BrowserManager()
    return _manager
