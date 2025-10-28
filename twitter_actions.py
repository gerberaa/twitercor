#!/usr/bin/env python3
"""
Extended Twitter API operations for interactions

This module contains the actual GraphQL operations for likes, retweets, etc.
"""

import asyncio
import json
import random
import httpx
from typing import Dict, Optional

from twscrape.queue_client import QueueClient
from twscrape.accounts_pool import AccountsPool
from twscrape.account import TOKEN  # Імпортуємо стандартний токен


# Known GraphQL operations for interactions
# These need to be updated with actual operation IDs from Twitter/X
GRAPHQL_OPERATIONS = {
    # Likes
    "FavoriteTweet": "lI07N6Otwv1PhnEgXILM7A/FavoriteTweet",
    "UnfavoriteTweet": "ZYKSe-w7KEslx3JhSIk5LA/UnfavoriteTweet",
    
    # Retweets
    "CreateRetweet": "ojPdsZsimiJrUGLR1sjUtA/CreateRetweet", 
    "DeleteRetweet": "iQtK4dl5hBmXewYosfmNlA/DeleteRetweet",
    
    # Follow
    "Follow": "7jQOD9v9vZG_xVkD5MlKEg/Follow",
    "Unfollow": "2Q7QqG3gnhJw6UyCPEhQ3A/Unfollow",
}

GQL_URL = "https://x.com/i/api/graphql"


class TwitterActionsAPI:
    """Extended API for Twitter interactions."""
    
    def __init__(self, pool: AccountsPool, debug=False, proxy: str = None):
        self.pool = pool
        self.debug = debug
        self.proxy = proxy

    async def _make_request(self, operation: str, variables: dict, queue_name: str = None) -> Optional[dict]:
        """Make a GraphQL request for Twitter actions."""
        try:
            # Отримуємо акаунт з пулу з більшою затримкою
            account = await self.pool.get_for_queue_or_wait(operation)
            if not account:
                print(f"No account available for {operation}")
                return None
                
            # КРИТИЧНО: Використовуємо проксі акаунта, якщо він є в базі twscrape
            account_proxy = account.proxy if hasattr(account, 'proxy') and account.proxy else self.proxy
            if self.debug and account_proxy:
                print(f"🌐 Using proxy for @{account.username}: {account_proxy[:30]}...")
            
            operation_id = GRAPHQL_OPERATIONS[operation].split("/")[0]
            operation_name = GRAPHQL_OPERATIONS[operation].split("/")[1] 
            url = f"{GQL_URL}/{operation_id}/{operation_name}"
            
            # Підготовуємо заголовки як в оригінальному twscrape
            headers = {
                "authorization": TOKEN,  # Використовуємо стандартний токен
                "content-type": "application/json",
                "x-twitter-auth-type": "OAuth2Session",
                "x-twitter-client-language": "en",
                "x-twitter-active-user": "yes",
                "user-agent": account.user_agent,
            }
            
            # Додаємо CSRF токен з cookies якщо є
            cookies_dict = account.cookies
            if isinstance(cookies_dict, str):
                # Якщо cookies - це рядок, конвертуємо в словник
                import json
                try:
                    cookies_dict = json.loads(cookies_dict) if cookies_dict else {}
                except:
                    cookies_dict = {}
            
            if "ct0" in cookies_dict:
                headers["x-csrf-token"] = cookies_dict["ct0"]
            
            # Підготовуємо дані для POST запиту
            payload = {
                "variables": variables,
                "queryId": operation_id
            }
            
            # Використовуємо httpx з проксі конкретного акаунта
            async with httpx.AsyncClient(
                cookies=cookies_dict,
                proxy=account_proxy,  # Використовуємо проксі акаунта
                timeout=30.0
            ) as client:
                response = await client.post(
                    url, 
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if self.debug:
                        print(f"Response for {operation}: {result}")
                    return result
                else:
                    print(f"Request failed with status {response.status_code}: {response.text[:200]}")
                    return None
                
        except Exception as e:
            print(f"Error in {operation}: {e}")
            import traceback
            traceback.print_exc()
            
        return None

    async def like_tweet(self, tweet_id: str) -> bool:
        """Like a tweet."""
        variables = {"tweet_id": str(tweet_id)}
        result = await self._make_request("FavoriteTweet", variables)
        
        if result:
            # Перевіряємо різні можливі структури відповіді
            if "data" in result:
                return True  # Якщо є секція data, вважаємо успішним
            elif "errors" in result:
                print(f"Twitter API error: {result['errors']}")
                return False
            else:
                # Якщо структура незрозуміла, виводимо для дебагу
                print(f"Unexpected response structure: {result}")
                return True  # Оптимістично вважаємо успішним
            
        return False

    async def unlike_tweet(self, tweet_id: str) -> bool:
        """Unlike a tweet."""
        variables = {"tweet_id": str(tweet_id)}
        result = await self._make_request("UnfavoriteTweet", variables)
        
        if result:
            if "data" in result:
                return True
            elif "errors" in result:
                print(f"Twitter API error: {result['errors']}")
                return False
            else:
                return True
            
        return False

    async def retweet(self, tweet_id: str) -> bool:
        """Retweet a tweet."""
        variables = {"tweet_id": str(tweet_id), "dark_request": False}
        result = await self._make_request("CreateRetweet", variables)
        
        if result:
            if "data" in result:
                return True
            elif "errors" in result:
                print(f"Twitter API error: {result['errors']}")
                return False
            else:
                return True
            
        return False

    async def unretweet(self, tweet_id: str) -> bool:
        """Unretweet a tweet."""
        variables = {"source_tweet_id": str(tweet_id), "dark_request": False}
        result = await self._make_request("DeleteRetweet", variables)
        
        if result:
            if "data" in result:
                return True
            elif "errors" in result:
                print(f"Twitter API error: {result['errors']}")
                return False
            else:
                return True
            
        return False

    async def follow_user(self, user_id: str) -> bool:
        """Follow a user."""
        variables = {"user_id": str(user_id)}
        result = await self._make_request("Follow", variables)
        
        if result and "data" in result:
            return result["data"].get("follow", {}).get("user", {}) is not None
            
        return False

    async def unfollow_user(self, user_id: str) -> bool:
        """Unfollow a user."""
        variables = {"user_id": str(user_id)}
        result = await self._make_request("Unfollow", variables)
        
        if result and "data" in result:
            return result["data"].get("unfollow", {}).get("user", {}) is not None
            
        return False


class RealisticEngagement:
    """Helper class for creating realistic engagement patterns."""
    
    def __init__(self, total_accounts: int):
        self.total_accounts = total_accounts
    
    def calculate_engagement(self, engagement_type: str = "auto") -> Dict[str, int]:
        """Calculate realistic engagement numbers."""
        if self.total_accounts == 0:
            return {"views": 0, "likes": 0, "retweets": 0}
        
        if engagement_type == "viral":
            # Viral content
            views_ratio = random.uniform(0.8, 0.95)
            likes_ratio = random.uniform(0.4, 0.7)
            retweets_ratio = 0.0  # ВИМКНЕНО: ретвіти повністю відключені
        elif engagement_type == "popular":
            # Popular content
            views_ratio = random.uniform(0.6, 0.8)
            likes_ratio = random.uniform(0.25, 0.45)
            retweets_ratio = 0.0  # ВИМКНЕНО: ретвіти повністю відключені
        elif engagement_type == "normal":
            # Normal content
            views_ratio = random.uniform(0.4, 0.6)
            likes_ratio = random.uniform(0.15, 0.3)
            retweets_ratio = 0.0  # ВИМКНЕНО: ретвіти повністю відключені
        elif engagement_type == "low":
            # Low engagement
            views_ratio = random.uniform(0.2, 0.4)
            likes_ratio = random.uniform(0.05, 0.15)
            retweets_ratio = 0.0  # ВИМКНЕНО: ретвіти повністю відключені
        else:  # auto
            # Automatically determine based on account count
            if self.total_accounts > 50:
                return self.calculate_engagement("popular")
            elif self.total_accounts > 20:
                return self.calculate_engagement("normal")
            else:
                return self.calculate_engagement("low")
        
        views = max(1, int(self.total_accounts * views_ratio))
        likes = max(1, int(self.total_accounts * likes_ratio))
        retweets = max(0, int(self.total_accounts * retweets_ratio))
        
        # Ensure we don't exceed total accounts
        views = min(views, self.total_accounts)
        likes = min(likes, self.total_accounts)
        retweets = min(retweets, self.total_accounts)
        
        return {
            "views": views,
            "likes": likes,
            "retweets": retweets
        }
    
    def get_random_delays(self, action_count: int, min_delay: int = 5, max_delay: int = 60) -> list:
        """Generate random delays between actions for natural behavior."""
        delays = []
        for _ in range(action_count):
            # Use exponential distribution for more realistic timing
            delay = random.expovariate(1 / ((min_delay + max_delay) / 2))
            delay = max(min_delay, min(max_delay, int(delay)))
            delays.append(delay)
        return delays
    
    def shuffle_accounts(self, accounts: list, action_type: str = "view") -> list:
        """Shuffle accounts based on action type for realistic patterns."""
        shuffled = accounts.copy()
        random.shuffle(shuffled)
        
        # For different actions, use different patterns
        if action_type == "like":
            # Likes tend to come from more engaged users
            # Put some accounts at the beginning more often
            engaged_accounts = shuffled[:len(shuffled)//3]
            other_accounts = shuffled[len(shuffled)//3:]
            
            # 70% chance to start with engaged accounts
            if random.random() < 0.7:
                return engaged_accounts + other_accounts
            else:
                return shuffled
        elif action_type == "retweet":
            # Retweets are more selective
            # Randomize but ensure we get different accounts each time
            return shuffled
        else:  # views
            # Views can be more random
            return shuffled


async def test_twitter_actions():
    """Test function for Twitter actions."""
    from twscrape import API
    
    api = API()
    actions_api = TwitterActionsAPI(api.pool, debug=True)
    
    # Test with a sample tweet ID (replace with real one)
    test_tweet_id = "1234567890"
    
    print(f"Testing actions on tweet: {test_tweet_id}")
    
    # Test like
    print("Testing like...")
    like_result = await actions_api.like_tweet(test_tweet_id)
    print(f"Like result: {like_result}")
    
    # Test retweet
    print("Testing retweet...")
    retweet_result = await actions_api.retweet(test_tweet_id)
    print(f"Retweet result: {retweet_result}")


if __name__ == "__main__":
    asyncio.run(test_twitter_actions())