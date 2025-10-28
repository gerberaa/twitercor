import asyncio
from twitter_automation import TwitterInteractionAPI, API
from playwright.async_api import async_playwright

async def playwright_view_tweet(tweet_url, username, proxy=None, cookies=None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(proxy={"server": proxy} if proxy else None, headless=True)
        context = await browser.new_context()
        if cookies:
            await context.add_cookies([
                {"name": "ct0", "value": cookies.get("ct0", ""), "domain": ".x.com", "path": "/"},
                {"name": "auth_token", "value": cookies.get("auth_token", ""), "domain": ".x.com", "path": "/"},
            ])
        page = await context.new_page()
        await page.goto(tweet_url)
        await asyncio.sleep(10)  # Чекаємо 10 секунд для більш реалістичного перегляду
        await browser.close()
        print(f"✅ Playwright перегляд твіта {tweet_url} акаунтом @{username}")

async def main():
    api = API()
    ti = TwitterInteractionAPI(api)
    tweet_url = "https://x.com/StillhazeE/status/1983157013225095655"
    # Отримуємо до 10 активних акаунтів
    accounts_info = await ti.pool.accounts_info()
    active_accounts = [a for a in accounts_info if a["active"]][:10]
    tasks = []
    for acc in active_accounts:
        username = acc["username"]
        proxy = ti.get_account_proxy(username)
        account = await ti.pool.get_account(username)
        cookies = account.cookies if account else {}
        tasks.append(playwright_view_tweet(tweet_url, username, proxy=proxy, cookies=cookies))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
