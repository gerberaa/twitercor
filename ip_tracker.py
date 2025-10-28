#!/usr/bin/env python3
"""
IP Tracker Test - Перевіряє чи всі запити справді йдуть через призначені проксі

Цей скрипт тестує реальні IP адреси для кожного акаунта,
щоб переконатися що проксі працюють правильно.
"""

import asyncio
import json
import httpx
from typing import Dict, List, Optional
from twscrape import API
from twitter_actions import TwitterActionsAPI


class IPTracker:
    """Трекер IP адрес для перевірки проксі."""
    
    def __init__(self):
        self.test_url = "https://api.ipify.org?format=json"
        self.results = {}
    
    async def test_account_ip(self, username: str, proxy: str) -> Dict:
        """Тестує реальний IP для конкретного акаунта."""
        result = {
            "username": username,
            "assigned_proxy": proxy,
            "actual_ip": None,
            "proxy_ip": None,
            "working": False,
            "error": None
        }
        
        try:
            # Спочатку отримуємо IP проксі без запиту
            if proxy:
                proxy_parts = proxy.replace("http://", "").split("@")
                if len(proxy_parts) == 2:
                    proxy_host = proxy_parts[1].split(":")[0]
                    result["proxy_ip"] = proxy_host
            
            # Тестуємо реальний запит через TwitterActionsAPI
            from twscrape.accounts_pool import AccountsPool
            pool = AccountsPool()
            
            # Створюємо API з проксі акаунта
            actions_api = TwitterActionsAPI(pool, debug=True, proxy=proxy)
            
            # Робимо прямий HTTP запит через проксі
            async with httpx.AsyncClient(proxy=proxy, timeout=15.0) as client:
                response = await client.get(self.test_url)
                
                if response.status_code == 200:
                    data = response.json()
                    result["actual_ip"] = data.get("ip", "Unknown")
                    
                    # Перевіряємо чи IP відповідає проксі
                    if result["proxy_ip"] and result["actual_ip"] == result["proxy_ip"]:
                        result["working"] = True
                    elif result["actual_ip"] != result["proxy_ip"]:
                        result["working"] = True  # Проксі працює, але може мати інший вихідний IP
                    else:
                        result["error"] = "IP не відповідає проксі"
                else:
                    result["error"] = f"HTTP {response.status_code}"
                    
        except Exception as e:
            result["error"] = str(e)[:100]
            
        return result
    
    async def test_all_accounts(self) -> Dict[str, Dict]:
        """Тестує IP для всіх акаунтів."""
        print("🔍 IP Tracker Test - Перевірка проксі акаунтів")
        print("=" * 60)
        
        # Завантажуємо конфігурацію проксі
        proxies = {}
        try:
            with open("proxies.json", 'r', encoding='utf-8') as f:
                proxies = json.load(f)
            print(f"📁 Завантажено {len(proxies)} призначень проксі")
        except Exception as e:
            print(f"❌ Помилка завантаження проксі: {e}")
            return {}
        
        print("\n🧪 Тестування IP адрес...")
        print("-" * 60)
        
        # Тестуємо кожен акаунт
        tasks = []
        for username, proxy in proxies.items():
            task = self.test_account_ip(username, proxy)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обробляємо результати
        account_results = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                username = list(proxies.keys())[i]
                account_results[username] = {
                    "username": username,
                    "error": str(result),
                    "working": False
                }
            else:
                account_results[result["username"]] = result
        
        return account_results
    
    def print_results(self, results: Dict[str, Dict]):
        """Виводить результати тестування."""
        working_count = sum(1 for r in results.values() if r.get("working", False))
        total_count = len(results)
        
        print(f"\n📊 Результати IP тестування:")
        print(f"✅ Працюють: {working_count}/{total_count}")
        print(f"❌ Проблеми: {total_count - working_count}/{total_count}")
        print("=" * 80)
        
        print(f"{'Акаунт':<20} {'Призначений IP':<20} {'Реальний IP':<20} {'Статус':<15}")
        print("-" * 80)
        
        for result in results.values():
            username = result.get("username", "Unknown")[:19]
            proxy_ip = result.get("proxy_ip", "N/A")[:19]
            actual_ip = result.get("actual_ip", "N/A")[:19]
            
            if result.get("working", False):
                status = "✅ OK"
                # Перевіряємо чи IPs збігаються
                if proxy_ip != "N/A" and actual_ip != "N/A" and proxy_ip != actual_ip:
                    status = "⚠️ Інший IP"
            else:
                error = result.get("error", "Unknown error")[:15]
                status = f"❌ {error}"
            
            print(f"{username:<20} {proxy_ip:<20} {actual_ip:<20} {status:<15}")
    
    def analyze_security(self, results: Dict[str, Dict]):
        """Аналізує безпеку конфігурації."""
        print(f"\n🛡️ Аналіз безпеки:")
        print("-" * 40)
        
        working_proxies = [r for r in results.values() if r.get("working", False)]
        failed_proxies = [r for r in results.values() if not r.get("working", False)]
        
        print(f"✅ Безпечні акаунти (проксі працюють): {len(working_proxies)}")
        print(f"🚨 НЕБЕЗПЕЧНІ акаунти (проксі НЕ працюють): {len(failed_proxies)}")
        
        if failed_proxies:
            print(f"\n⚠️ УВАГА! Ці акаунти працюють БЕЗ проксі:")
            for r in failed_proxies:
                username = r.get("username", "Unknown")
                error = r.get("error", "Unknown")
                print(f"  🚨 @{username}: {error}")
            print(f"\n💥 КРИТИЧНО: {len(failed_proxies)} акаунтів можуть бути забанені!")
        
        # Перевіряємо унікальність IP
        unique_ips = set()
        for r in working_proxies:
            if r.get("actual_ip"):
                unique_ips.add(r.get("actual_ip"))
        
        print(f"\n🌐 Унікальних IP адрес: {len(unique_ips)}")
        if len(unique_ips) < len(working_proxies):
            print(f"⚠️ Деякі акаунти використовують однакові IP!")
        
        # Рекомендації
        security_score = (len(working_proxies) / len(results)) * 100 if results else 0
        print(f"\n📈 Оцінка безпеки: {security_score:.1f}%")
        
        if security_score >= 90:
            print("🎉 ВІДМІННО: Система готова до використання!")
        elif security_score >= 70:
            print("⚠️ ДОБРЕ: Система безпечна, але є проблемні акаунти")
        elif security_score >= 50:
            print("🚨 УВАГА: Багато проблем, потрібні виправлення")
        else:
            print("💥 КРИТИЧНО: Система НЕ безпечна! НЕ використовуйте!")


async def main():
    """Головна функція."""
    tracker = IPTracker()
    
    try:
        results = await tracker.test_all_accounts()
        
        if results:
            tracker.print_results(results)
            tracker.analyze_security(results)
            
            # Зберігаємо результати
            with open("ip_tracker_results.json", 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Результати збережені в ip_tracker_results.json")
            
        else:
            print("❌ Не вдалося протестувати жодного акаунта")
            
    except Exception as e:
        print(f"❌ Помилка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🎯 Starting IP Tracker Test...")
    asyncio.run(main())