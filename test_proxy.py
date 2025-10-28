#!/usr/bin/env python3
"""
Quick proxy test script
"""
import asyncio
import httpx

async def test_proxy_quick(proxy_string):
    """Test a single proxy quickly."""
    print(f"🔄 Тестуємо проксі: {proxy_string}")
    
    # Переконуємося що проксі має правильний формат
    if not proxy_string.startswith(('http://', 'https://', 'socks5://')):
        proxy_string = 'http://' + proxy_string
    
    print(f"🔗 Повний URL: {proxy_string}")
    
    test_urls = [
        "http://ip-api.com/json/",
        "https://api.ipify.org?format=json",
        "http://httpbin.org/ip"
    ]
    
    try:
        async with httpx.AsyncClient(proxy=proxy_string, timeout=15.0) as client:
            for i, url in enumerate(test_urls, 1):
                try:
                    print(f"📡 Тест {i}: {url}")
                    response = await client.get(url)
                    print(f"📊 Статус: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            ip = data.get('query') or data.get('ip') or data.get('origin', 'Unknown')
                            print(f"✅ IP: {ip}")
                            print(f"✅ Проксі працює через {url}")
                            return True
                        except:
                            print(f"✅ Підключення успішне (не JSON відповідь)")
                            return True
                    else:
                        print(f"❌ HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Помилка з {url}: {str(e)[:100]}")
                    continue
                    
        print("❌ Всі тести не вдалися")
        return False
        
    except Exception as e:
        print(f"❌ Загальна помилка: {str(e)}")
        return False

async def main():
    # Ваш проксі
    proxy = "RQQ6C0VF:MZH4VXZU@213.145.79.139:48832"
    
    print("="*60)
    print("🧪 ШВИДКИЙ ТЕСТ ПРОКСІ")
    print("="*60)
    print()
    
    success = await test_proxy_quick(proxy)
    
    print()
    print("="*60)
    if success:
        print("🎉 ПРОКСІ ПРАЦЮЄ!")
    else:
        print("💥 ПРОКСІ НЕ ПРАЦЮЄ")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())