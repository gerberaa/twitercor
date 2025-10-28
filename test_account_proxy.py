#!/usr/bin/env python3
"""
Тест для перевірки використання проксі акаунтами
"""
import asyncio
from twitter_automation import TwitterAutomation
from twscrape import API

async def test_account_proxy():
    """Тестуємо чи акаунти використовують проксі"""
    print("🔍 Тестування використання проксі акаунтами")    
    print("=" * 50)
    
    api = API()
    accounts = await api.pool.accounts_info()
    
    if not accounts:
        print("❌ Акаунти не знайдено!")
        return
        
    print(f"👥 Знайдено {len(accounts)} акаунтів")
    print()
    
    # Тестуємо перший акаунт
    test_account = accounts[0]
    username = test_account['username']
    
    print(f"🧪 Тестування акаунту: @{username}")
    
    try:
        # Створюємо TwitterAutomation і тестуємо API
        automation = TwitterAutomation(api)
        actions_api = automation.create_actions_api_for_account(username)
        
        if actions_api:
            print(f"✅ API створено для @{username}")
            
            # Перевіряємо IP через httpx
            import httpx
            if hasattr(actions_api, '_client') and actions_api._client:
                # Отримуємо проксі з клієнта
                proxy_info = getattr(actions_api._client, '_proxies', 'No proxy info')
                print(f"🌐 Проксі клієнта: {proxy_info}")
                
            # Тестуємо запит на отримання IP
            try:
                async with httpx.AsyncClient(
                    proxies=actions_api.proxy if hasattr(actions_api, 'proxy') else None,
                    timeout=10
                ) as client:
                    response = await client.get('https://httpbin.org/ip')
                    ip_data = response.json()
                    print(f"🔗 IP адреса через проксі: {ip_data.get('origin', 'Unknown')}")
            except Exception as e:
                print(f"⚠️ Помилка отримання IP: {e}")
                
        else:
            print(f"❌ Не вдалося створити API для @{username}")
            
    except Exception as e:
        print(f"❌ Помилка тестування: {e}")

if __name__ == "__main__":
    asyncio.run(test_account_proxy())