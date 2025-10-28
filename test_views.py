import asyncio
from twitter_automation import TwitterAutomation, API

tweet_url = "https://x.com/StillhazeE/status/1983157013225095655"

async def test_views():
    api = API()
    automation = TwitterAutomation(api)
    result = await automation.process_tweet_url(tweet_url, likes_count=0, retweets_count=0, views_count=10)
    print("Результат накрутки переглядів:")
    print(result)

if __name__ == "__main__":
    asyncio.run(test_views())
