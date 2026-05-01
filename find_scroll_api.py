import asyncio
import os
import sys
from playwright.async_api import async_playwright

# Usage: python find_scroll_api.py <substack_handle>
# Intercepts Substack API calls made during page load and scrolling.
# Set SUBSTACK_SESSION_COOKIE env var to authenticate.

if len(sys.argv) < 2:
    print("Usage: python find_scroll_api.py <substack_handle>")
    print("Example: python find_scroll_api.py thepillarsofwisdom")
    sys.exit(1)

HANDLE = sys.argv[1]
URL = f"https://substack.com/@{HANDLE}/notes"
SESSION_COOKIE = os.environ.get("SUBSTACK_SESSION_COOKIE", "")

async def find_api():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        if SESSION_COOKIE:
            await context.add_cookies([{
                "name": "substack.sid",
                "value": SESSION_COOKIE,
                "domain": ".substack.com",
                "path": "/",
            }])

        page = await context.new_page()

        api_calls = []

        async def handle_request(request):
            url = request.url
            if "api/v1" in url or "substack.com/api" in url:
                api_calls.append(f"REQ  {request.method} {url}")

        async def handle_response(response):
            url = response.url
            if "api/v1" in url or "substack.com/api" in url:
                try:
                    body = await response.json()
                    items = body.get("items", []) if isinstance(body, dict) else []
                    count = len(items)
                    api_calls.append(f"RESP {response.status} {url} → {count} items")
                except:
                    api_calls.append(f"RESP {response.status} {url}")

        page.on("request", handle_request)
        page.on("response", handle_response)

        print("Loading page...")
        await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)

        print("=== API calls on page load ===")
        for c in api_calls:
            print(" ", c)
        api_calls.clear()

        print("\nScrolling...")
        for i in range(5):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1500)
            await page.keyboard.press("End")
            await page.wait_for_timeout(800)

            btn = await page.query_selector('button:has-text("More")')
            if btn:
                await btn.click()
                await page.wait_for_timeout(1500)

        print(f"\n=== API calls during scroll ===")
        for c in api_calls:
            print(" ", c)

        await browser.close()

asyncio.run(find_api())
