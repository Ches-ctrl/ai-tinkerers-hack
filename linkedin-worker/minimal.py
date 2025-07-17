import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('https://www.google.com')
        await page.wait_for_timeout(10000)
        await browser.close()

asyncio.run(run())
