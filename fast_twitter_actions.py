#!/usr/bin/env python3
"""
Fast Twitter Actions API - з зменшеними затримками

Цей модуль обходить стандартні затримки twscrape для швидшої роботи.
"""

import asyncio
import json
import random
import httpx
import time
from typing import Dict, Optional
from datetime import datetime, timedelta

from twscrape.accounts_pool import AccountsPool
from twscrape.account import TOKEN
from twscrape.api import GQL_FEATURES
from twitter_actions import TwitterActionsAPI, GRAPHQL_OPERATIONS


class FastTwitterActionsAPI:
    """
    Швидка версія TwitterActionsAPI з власним управлінням затримками
    """
    
    def __init__(self, pool: AccountsPool, debug: bool = False, proxy: str = None):
        self.pool = pool
        self.debug = debug
        self.proxy = proxy
        # Власна система затримок - зберігаємо час останнього запиту для кожного акаунта
        self.account_last_request = {}
        # Мінімальна затримка між запитами (секунди) - збільшено для безпеки
        self.min_delay = 30  # 30 секунд для безпеки акаунтів
        
    async def _get_account_with_minimal_delay(self, queue_name: str = "FavoriteTweet"):
        """Отримати акаунт з мінімальною затримкою"""
        accounts_info = await self.pool.accounts_info()
        active_accounts = [acc for acc in accounts_info if acc["active"]]
        
        if not active_accounts:
            return None
            
        # Знайдемо акаунт, який найдавніше використовувався
        best_account = None
        best_wait_time = float('inf')
        
        current_time = time.time()
        
        for acc_info in active_accounts:
            username = acc_info["username"]
            last_request_time = self.account_last_request.get(username, 0)
            wait_time = max(0, self.min_delay - (current_time - last_request_time))
            
            if wait_time < best_wait_time:
                best_wait_time = wait_time
                best_account = username
        
        if best_account and best_wait_time > 0:
            if self.debug:
                print(f"Waiting {best_wait_time:.1f}s for account {best_account}")
            await asyncio.sleep(best_wait_time)
        
        # Отримуємо повний об'єкт акаунта
        account = await self.pool.get(best_account)
        if account:
            self.account_last_request[best_account] = time.time()
        
        return account
    
    async def _make_direct_request(self, operation: str, variables: Dict, account = None):
        """Виконати прямий GraphQL запит без обмежень twscrape"""
        if not account:
            account = await self._get_account_with_minimal_delay()
            
        if not account:
            return None
            
        url = f"https://x.com/i/api/graphql/{GRAPHQL_OPERATIONS[operation]}"
        
        # Отримуємо CSRF токен з cookies
        csrf_token = account.cookies.get('ct0', '')
        
        # Перетворюємо cookies словник в строку
        cookie_string = "; ".join([f"{k}={v}" for k, v in account.cookies.items()])
        
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "X-Csrf-Token": csrf_token,
            "Cookie": cookie_string,
            "User-Agent": account.user_agent,
        }
        
        data = {
            "variables": variables,
            "features": GQL_FEATURES,
        }

        # Використовуємо проксі для безпеки акаунтів
        try:
            async with httpx.AsyncClient(proxy=self.proxy, timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=data)
                if self.debug:
                    print(f"🔗 Request to {operation}: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    return result
                else:
                    print(f"❌ Request failed: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            print(f"❌ Request error: {e}")
            return None
    
    async def like_tweet(self, tweet_id: str) -> bool:
        """Лайкнути твіт"""
        variables = {"tweet_id": tweet_id}
        result = await self._make_direct_request("FavoriteTweet", variables)
        return result is not None
    
    async def unlike_tweet(self, tweet_id: str) -> bool:
        """Прибрати лайк з твіта"""
        variables = {"tweet_id": tweet_id}
        result = await self._make_direct_request("UnfavoriteTweet", variables)
        return result is not None
    
    async def retweet(self, tweet_id: str) -> bool:
        """Ретвітнути твіт"""
        variables = {"tweet_id": tweet_id, "dark_request": False}
        result = await self._make_direct_request("CreateRetweet", variables)
        return result is not None
    
    async def unretweet(self, tweet_id: str) -> bool:
        """Прибрати ретвіт"""
        variables = {"source_tweet_id": tweet_id, "dark_request": False}
        result = await self._make_direct_request("DeleteRetweet", variables)
        return result is not None
    
    async def view_tweet(self, tweet_id: str) -> bool:
        """Переглянути твіт (емуляція)"""
        # Для переглядів просто робимо невелику затримку
        await asyncio.sleep(random.uniform(0.5, 1.5))
        return True