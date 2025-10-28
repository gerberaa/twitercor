#!/usr/bin/env python3
"""
Extended API for Twitter/X interactions (likes, retweets, views)

This module extends the basic twscrape API to include interaction functionality.
"""

import asyncio
import json
import re
import random
from typing import Dict, List, Optional
from urllib.parse import urlparse, parse_qs

from twscrape.api import API, GQL_URL, GQL_FEATURES
from twscrape.queue_client import QueueClient
from twscrape.utils import encode_params
from twitter_actions import TwitterActionsAPI
from fast_twitter_actions import FastTwitterActionsAPI
from playwright.async_api import async_playwright


class TwitterInteractionAPI:
    async def fake_view_tweet(self, tweet_id: str, username: str = None) -> bool:
        """Імітує перегляд твіта через GET-запит на сторінку твіта."""
        try:
            # Визначаємо username акаунта
            if username:
                account_proxy = self.get_account_proxy(username)
                account = await self.pool.get_account(username)
            else:
                account_proxy = None
                account = None
            # Формуємо URL твіта
            tweet_url = f"https://x.com/i/web/status/{tweet_id}"
            import httpx
            headers = {
                "User-Agent": account.user_agent if account and hasattr(account, "user_agent") else "Mozilla/5.0",
                "Accept": "text/html,application/xhtml+xml,application/xml",
                "Accept-Language": "en-US,en;q=0.9",
            }
            cookies = account.cookies if account else {}
            async with httpx.AsyncClient(proxy=account_proxy, headers=headers, cookies=cookies, timeout=20.0) as client:
                response = await client.get(tweet_url)
                if response.status_code == 200:
                    print(f"✅ Перегляд твіта {tweet_id} акаунтом @{username}")
                    return True
                else:
                    print(f"❌ Не вдалося переглянути твіт {tweet_id} акаунтом @{username}: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Помилка перегляду твіта {tweet_id} акаунтом @{username}: {e}")
            return False
    def __init__(self, api: API):
        self.api = api
        self.pool = api.pool
        self.debug = api.debug
        self.proxy = api.proxy
        self.actions = TwitterActionsAPI(self.pool, debug=self.debug, proxy=self.proxy)
        # Завантажуємо проксі для акаунтів
        self.account_proxies = self._load_account_proxies()
    
    def _load_account_proxies(self) -> Dict[str, str]:
        """Load proxy assignments for accounts."""
        import os
        import json
        
        # Спочатку пробуємо завантажити валідовані проксі
        working_proxy_file = "proxies_working.json"
        if os.path.exists(working_proxy_file):
            try:
                with open(working_proxy_file, 'r', encoding='utf-8') as f:
                    proxies = json.load(f)
                    print(f"✅ Завантажено {len(proxies)} перевірених проксі")
                    return proxies
            except Exception as e:
                print(f"⚠️ Помилка завантаження перевірених проксі: {e}")
        
        # Якщо немає валідованих, завантажуємо звичайні
        proxy_file = "proxies.json"
        if os.path.exists(proxy_file):
            try:
                with open(proxy_file, 'r', encoding='utf-8') as f:
                    proxies = json.load(f)
                    print(f"⚠️ Завантажено {len(proxies)} проксі (не перевірених)")
                    print("💡 Запустіть proxy_validator.py щоб спочатку перевірити проксі!")
                    return proxies
            except Exception as e:
                print(f"❌ Помилка завантаження проксі: {e}")
                
        print("❌ Конфігурацію проксі не знайдено!")
        print("🚨 Це небезпечно - всі запити будуть прямими!")
        return {}
    
    def get_account_proxy(self, username: str) -> Optional[str]:
        """Get proxy for specific account."""
        return self.account_proxies.get(username, None)
    
    def create_actions_api_for_account(self, username: str) -> TwitterActionsAPI:
        """Create TwitterActionsAPI instance with account's proxy."""
        account_proxy = self.get_account_proxy(username)
        if self.debug and account_proxy:
            print(f"🌐 Використовується проксі для @{username}: {account_proxy}")
        return TwitterActionsAPI(self.pool, debug=self.debug, proxy=account_proxy)

    def extract_tweet_id(self, url: str) -> Optional[str]:
        """Extract tweet ID from Twitter URL."""
        # Various Twitter URL formats:
        # https://x.com/username/status/1234567890
        # https://twitter.com/username/status/1234567890
        # https://x.com/i/status/1234567890
        patterns = [
            r'(?:twitter\.com|x\.com)/.+/status/(\d+)',
            r'(?:twitter\.com|x\.com)/i/status/(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # If it's just a number, assume it's already a tweet ID
        if url.isdigit():
            return url
            
        return None

    async def like_tweet(self, tweet_id: str, username: str = None) -> bool:
        """Like a tweet using a specific account or random account."""
        try:
            # Створюємо окремий екземпляр TwitterActionsAPI з проксі для конкретного акаунта
            if username:
                account_proxy = self.get_account_proxy(username)
                actions = TwitterActionsAPI(self.pool, debug=self.debug, proxy=account_proxy)
            else:
                actions = self.actions
                
            return await actions.like_tweet(tweet_id)
        except Exception as e:
            print(f"Помилка лайку твіту {tweet_id}: {e}")
            return False

    async def unlike_tweet(self, tweet_id: str, username: str = None) -> bool:
        """Unlike a tweet using a specific account or random account."""
        try:
            if username:
                account_proxy = self.get_account_proxy(username)
                actions = TwitterActionsAPI(self.pool, debug=self.debug, proxy=account_proxy)
            else:
                actions = self.actions
                
            return await actions.unlike_tweet(tweet_id)
        except Exception as e:
            print(f"Помилка видалення лайку твіту {tweet_id}: {e}")
            return False

    async def retweet(self, tweet_id: str, username: str = None) -> bool:
        """Retweet a tweet using a specific account or random account."""
        try:
            if username:
                account_proxy = self.get_account_proxy(username)
                actions = TwitterActionsAPI(self.pool, debug=self.debug, proxy=account_proxy)
            else:
                actions = self.actions
                
            return await actions.retweet(tweet_id)
        except Exception as e:
            print(f"Помилка ретвіту твіту {tweet_id}: {e}")
            return False

    async def view_tweet(self, tweet_id: str, username: str = None) -> bool:
        """View a tweet using a specific account."""
        try:
            # Для перегляду достатньо просто отримати детальну інформацію про твіт
            if username:
                account_proxy = self.get_account_proxy(username)
                # Створюємо тимчасовий API з проксі акаунта
                api = API(self.pool, debug=self.debug, proxy=account_proxy)
            else:
                api = self.api
                
            # Отримуємо твіт через TweetDetail API (це рахується як перегляд)
            try:
                # Використовуємо той самий метод що і get_tweet_stats
                tweet_data = await api._gql_item(
                    "_8aYOgEDz35BrBcBal1-_w/TweetDetail",
                    {"focalTweetId": str(tweet_id), "with_rux_injections": True,
                     "includePromotedContent": True, "withCommunity": True,
                     "withQuickPromoteEligibilityTweetFields": True,
                     "withBirdwatchNotes": True, "withVoice": True,
                     "withV2Timeline": True}
                )
                
                if tweet_data and tweet_data.status_code == 200:
                    return True
                else:
                    return False
                    
            except Exception:
                return False
                
        except Exception as e:
            if self.debug:
                print(f"Помилка перегляду твіту {tweet_id}: {e}")
            return False
        """Unretweet a tweet using a specific account or random account."""
        try:
            if username:
                account_proxy = self.get_account_proxy(username)
                actions = TwitterActionsAPI(self.pool, debug=self.debug, proxy=account_proxy)
            else:
                actions = self.actions
                
            return await actions.unretweet(tweet_id)
        except Exception as e:
            print(f"Помилка скасування ретвіту твіту {tweet_id}: {e}")
            return False

    async def view_tweet(self, tweet_id: str, username: str = None) -> bool:
        """View a tweet (increase view count) using a specific account or random account."""
        try:
            # Getting tweet details counts as a view
            tweet = await self.api.tweet_details(int(tweet_id))
            return tweet is not None
            
        except Exception as e:
            print(f"Error viewing tweet {tweet_id}: {e}")
            
        return False

    async def get_tweet_stats(self, tweet_id: str) -> Optional[Dict]:
        """Get current stats of a tweet."""
        try:
            tweet = await self.api.tweet_details(int(tweet_id))
            if tweet:
                return {
                    "likes": tweet.likeCount,
                    "retweets": tweet.retweetCount,
                    "replies": tweet.replyCount,
                    "views": tweet.viewCount if hasattr(tweet, 'viewCount') else 0,
                    "quotes": tweet.quoteCount if hasattr(tweet, 'quoteCount') else 0
                }
        except Exception as e:
            print(f"Error getting tweet stats {tweet_id}: {e}")
            
        return None

    async def playwright_view_tweet(self, tweet_id: str, username: str = None) -> bool:
        """Імітує перегляд твіта через Playwright з авторизацією і проксі."""
        try:
            tweet_url = f"https://x.com/i/web/status/{tweet_id}"
            account_proxy = self.get_account_proxy(username) if username else None
            account = await self.pool.get_account(username) if username else None
            cookies = account.cookies if account else {}
            async with async_playwright() as p:
                browser = await p.chromium.launch(proxy={"server": account_proxy} if account_proxy else None, headless=True)
                context = await browser.new_context()
                if cookies:
                    await context.add_cookies([
                        {"name": "ct0", "value": cookies.get("ct0", ""), "domain": ".x.com", "path": "/"},
                        {"name": "auth_token", "value": cookies.get("auth_token", ""), "domain": ".x.com", "path": "/"},
                    ])
                page = await context.new_page()
                await page.goto(tweet_url)
                await asyncio.sleep(10)
                await browser.close()
                print(f"✅ Playwright перегляд твіта {tweet_url} акаунтом @{username}")
                return True
        except Exception as e:
            print(f"❌ Playwright помилка перегляду твіта {tweet_id} акаунтом @{username}: {e}")
            return False


class TwitterAutomation:
    """Main automation class for managing multiple accounts and interactions."""
    
    def __init__(self, api: API, fast_mode: bool = True):
        self.api = api
        self.interaction_api = TwitterInteractionAPI(api)
        self.fast_mode = fast_mode
        
    def create_actions_api_for_account(self, username: str):
        """Create an API instance with the specific proxy for the account."""
        account_proxy = self.interaction_api.get_account_proxy(username)
        
        # Використовуємо стандартний TwitterActionsAPI який працював з проксі
        return TwitterActionsAPI(self.api.pool, debug=self.api.debug, proxy=account_proxy)
        
    async def get_active_accounts(self) -> List[str]:
        """Get list of active account usernames."""
        accounts_info = await self.api.pool.accounts_info()
        return [acc["username"] for acc in accounts_info if acc["active"]]

    async def process_tweet_url(self, tweet_url: str, likes_count: int = None, 
                               retweets_count: int = None, views_count: int = None) -> Dict:
        """Process a tweet URL with specified engagement numbers."""
        
        tweet_id = self.interaction_api.extract_tweet_id(tweet_url)
        if not tweet_id:
            return {"error": "Invalid tweet URL"}
        
        print(f"🎯 Обробка твіту: {tweet_url}")
        print(f"📊 Tweet ID: {tweet_id}")
        
        # Get initial stats
        initial_stats = await self.interaction_api.get_tweet_stats(tweet_id)
        if initial_stats:
            print(f"📈 Initial stats: {initial_stats}")
        
        active_accounts = await self.get_active_accounts()
        if not active_accounts:
            return {"error": "No active accounts available"}
        
        print(f"👥 Available accounts: {len(active_accounts)}")
        
        results = {
            "tweet_id": tweet_id,
            "tweet_url": tweet_url,
            "initial_stats": initial_stats,
            "actions": {
                "likes": 0,
                "retweets": 0,
                "views": 0
            },
            "errors": []
        }
        
        # Shuffle accounts for more realistic behavior
        shuffled_accounts = active_accounts.copy()
        random.shuffle(shuffled_accounts)
        
        # Initialize account lists
        likes_accounts = []
        retweet_accounts = []
        
        # Process likes with parallel execution (max 2 concurrent for safety)
        if likes_count and likes_count > 0:
            print(f"❤️ Adding {likes_count} likes (parallel processing with max 2 concurrent)...")
            likes_accounts = shuffled_accounts[:min(likes_count, len(shuffled_accounts))]
            
            # Виконуємо лайки паралельно групами по 2 для безпеки
            semaphore = asyncio.Semaphore(2)  # Максимум 2 одночасних операцій для безпеки
            
            async def process_like(account, index):
                async with semaphore:
                    try:
                        # Додаємо затримку перед першою дією для реалістичності
                        if index > 0:
                            delay = random.randint(30, 90)  # Збільшено затримку для безпеки
                            await asyncio.sleep(delay)
                        
                        # Створюємо окремий API з проксі для цього акаунта
                        actions_api = self.create_actions_api_for_account(account)
                        success = await actions_api.like_tweet(tweet_id)
                        
                        if success:
                            results["actions"]["likes"] += 1
                            print(f"✅ @{account} liked the tweet")
                            return True
                        else:
                            print(f"❌ @{account} failed to like the tweet")
                            results["errors"].append(f"Like failed for @{account}")
                            return False
                            
                    except Exception as e:
                        print(f"❌ Error with @{account} liking: {e}")
                        results["errors"].append(f"Like error for @{account}: {e}")
                        return False
            
            # Запускаємо всі лайки паралельно
            like_tasks = [process_like(account, i) for i, account in enumerate(likes_accounts)]
            await asyncio.gather(*like_tasks, return_exceptions=True)
            
            # Додаємо затримку між групами операцій
            if retweets_count or views_count:
                delay = random.randint(60, 180)  # Збільшено затримку між групами
                print(f"⏳ Waiting {delay} seconds before next operation group...")
                await asyncio.sleep(delay)
        
        # Process retweets with parallel execution (max 2 concurrent for safety)
        # ВИМКНЕНО: Ретвіти повністю відключені
        if False and retweets_count and retweets_count > 0:
            print(f"🔄 Adding {retweets_count} retweets (parallel processing with max 2 concurrent)...")
            # Use different accounts for retweets
            used_accounts = likes_accounts if likes_count else []
            remaining_accounts = [acc for acc in shuffled_accounts if acc not in used_accounts]
            retweet_accounts = remaining_accounts[:min(retweets_count, len(remaining_accounts))]
            
            # Виконуємо ретвіти паралельно групами по 2 для безпеки
            semaphore = asyncio.Semaphore(2)
            
            async def process_retweet(account, index):
                async with semaphore:
                    try:
                        # Додаємо затримку для реалістичності
                        if index > 0:
                            delay = random.randint(45, 120)  # Збільшено затримку для безпеки
                            await asyncio.sleep(delay)
                        
                        # Створюємо окремий API з проксі для цього акаунта
                        actions_api = self.create_actions_api_for_account(account)
                        success = await actions_api.retweet(tweet_id)
                        
                        if success:
                            results["actions"]["retweets"] += 1
                            print(f"✅ @{account} retweeted the tweet")
                            return True
                        else:
                            print(f"❌ @{account} failed to retweet the tweet")
                            results["errors"].append(f"Retweet failed for @{account}")
                            return False
                            
                    except Exception as e:
                        print(f"❌ Error with @{account} retweeting: {e}")
                        results["errors"].append(f"Retweet error for @{account}: {e}")
                        return False
            
            # Запускаємо всі ретвіти паралельно
            retweet_tasks = [process_retweet(account, i) for i, account in enumerate(retweet_accounts)]
            await asyncio.gather(*retweet_tasks, return_exceptions=True)
            
            # Додаємо затримку перед переглядами
            if views_count:
                delay = random.randint(90, 240)  # Збільшено затримку перед переглядами
                print(f"⏳ Waiting {delay} seconds before views...")
                await asyncio.sleep(delay)
        
        # Process views with parallel execution (max 3 concurrent for safety)
        if views_count and views_count > 0:
            print(f"👀 Adding {views_count} views (parallel processing with max 3 concurrent)...")
            # All accounts can view
            used_accounts_set = set(likes_accounts + retweet_accounts)
            view_accounts = [acc for acc in shuffled_accounts if acc not in used_accounts_set][:min(views_count, len(shuffled_accounts))]
            
            # Виконуємо перегляди паралельно групами по 3 для безпеки
            semaphore = asyncio.Semaphore(3)
            
            async def process_view(account, index):
                async with semaphore:
                    try:
                        # Додаємо мінімальну затримку для переглядів
                        for repeat in range(5):  # Збільшуємо до 5 повторів
                            if index > 0 or repeat > 0:
                                delay = random.randint(15, 45)
                                await asyncio.sleep(delay)
                            success = await self.interaction_api.playwright_view_tweet(tweet_id, username=account)
                            if success:
                                results["actions"]["views"] += 1
                                print(f"✅ @{account} viewed the tweet (раз {repeat+1})")
                            else:
                                print(f"❌ @{account} failed to view the tweet (раз {repeat+1})")
                                results["errors"].append(f"View failed for @{account} (раз {repeat+1})")
                        return True
                    except Exception as e:
                        print(f"❌ Error with @{account} viewing: {e}")
                        results["errors"].append(f"View error for @{account}: {e}")
                        return False
            
            # Запускаємо всі перегляди паралельно
            view_tasks = [process_view(account, i) for i, account in enumerate(view_accounts)]
            await asyncio.gather(*view_tasks, return_exceptions=True)
        
        # Get final stats
        final_stats = await self.interaction_api.get_tweet_stats(tweet_id)
        if final_stats:
            print(f"📊 Final stats: {final_stats}")
            results["final_stats"] = final_stats
        
        print(f"✅ Processing complete!")
        print(f"📈 Actions performed: {results['actions']}")
        
        # Додаткова статистика
        total_errors = len(results['errors'])
        total_attempts = likes_count + retweets_count + views_count
        success_rate = ((results['actions']['likes'] + results['actions']['retweets'] + results['actions']['views']) / total_attempts * 100) if total_attempts > 0 else 0
        
        print(f"📊 Success rate: {success_rate:.1f}%")
        if total_errors > 0:
            print(f"⚠️ Errors: {total_errors}")
        
        return results

    async def auto_engage_tweet(self, tweet_url: str) -> Dict:
        """Automatically engage with a tweet using realistic numbers."""
        
        active_accounts = await self.get_active_accounts()
        total_accounts = len(active_accounts)
        
        if total_accounts == 0:
            return {"error": "No active accounts available"}
        
        # Calculate realistic engagement numbers
        # Views: 60-80% of accounts
        views_count = random.randint(int(total_accounts * 0.6), int(total_accounts * 0.8))
        
        # Likes: 20-40% of accounts
        likes_count = random.randint(int(total_accounts * 0.2), int(total_accounts * 0.4))
        
        # Retweets: ВИМКНЕНО - ретвіти повністю відключені
        retweets_count = 0  # ВИМКНЕНО: ретвіти повністю відключені
        
        print(f"🤖 Auto-engaging with realistic numbers:")
        print(f"👥 Total accounts: {total_accounts}")
        print(f"👀 Views: {views_count}")
        print(f"❤️ Likes: {likes_count}")
        print(f"🔄 Retweets: {retweets_count} (ВІДКЛЮЧЕНО)")
        
        return await self.process_tweet_url(tweet_url, likes_count, retweets_count, views_count)