from __future__ import annotations

from contextlib import asynccontextmanager


class BrowserManager:
    def __init__(self, headless: bool = True):
        self.headless = headless

    @asynccontextmanager
    async def page(self):
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise RuntimeError("Playwright is required for browser applications") from exc
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            try:
                yield page
            finally:
                await browser.close()
