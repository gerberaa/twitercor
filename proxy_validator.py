#!/usr/bin/env python3
"""
Proxy Validator - Перевіряє всі проксі перед використанням
"""

import asyncio
import json
import httpx
from typing import Dict, List, Optional


class ProxyValidator:
    """Клас для валідації проксі."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.test_urls = [
            "http://ip-api.com/json/",
            "https://api.ipify.org?format=json",
            "http://httpbin.org/ip"
        ]
    
    async def test_single_proxy(self, proxy: str, test_url: str = None) -> Dict:
        """Тестує один проксі."""
        if not test_url:
            test_url = self.test_urls[0]
            
        result = {
            "proxy": proxy,
            "working": False,
            "ip": None,
            "response_time": None,
            "error": None
        }
        
        try:
            # Переконуємося що проксі має правильний формат
            if not proxy.startswith(('http://', 'https://', 'socks5://')):
                proxy = 'http://' + proxy
            
            import time
            start_time = time.time()
            
            async with httpx.AsyncClient(proxy=proxy, timeout=self.timeout) as client:
                response = await client.get(test_url)
                
                end_time = time.time()
                result["response_time"] = round(end_time - start_time, 2)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        result["ip"] = data.get('query') or data.get('ip') or data.get('origin', 'Unknown')
                        result["working"] = True
                    except:
                        result["working"] = True  # Підключення працює, навіть якщо не JSON
                        result["ip"] = "Connected"
                else:
                    result["error"] = f"HTTP {response.status_code}"
                    
        except Exception as e:
            result["error"] = str(e)[:100]  # Обрізаємо довгі помилки
            
        return result
    
    async def test_all_proxies(self, proxies: Dict[str, str]) -> Dict[str, Dict]:
        """Тестує всі проксі паралельно."""
        print(f"🧪 Testing {len(proxies)} proxies...")
        
        tasks = []
        for username, proxy in proxies.items():
            task = self.test_single_proxy(proxy)
            tasks.append((username, task))
        
        results = {}
        completed_tasks = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        for i, (username, _) in enumerate(tasks):
            if isinstance(completed_tasks[i], Exception):
                results[username] = {
                    "proxy": proxies[username],
                    "working": False,
                    "error": str(completed_tasks[i])
                }
            else:
                results[username] = completed_tasks[i]
        
        return results
    
    def print_results(self, results: Dict[str, Dict]):
        """Виводить результати тестування."""
        working_count = sum(1 for r in results.values() if r["working"])
        total_count = len(results)
        
        print(f"\n📊 Proxy Test Results:")
        print(f"✅ Working: {working_count}/{total_count}")
        print(f"❌ Failed: {total_count - working_count}/{total_count}")
        print("=" * 60)
        
        for username, result in results.items():
            status = "✅" if result["working"] else "❌"
            proxy = result["proxy"][:30] + "..." if len(result["proxy"]) > 30 else result["proxy"]
            
            if result["working"]:
                ip = result.get("ip", "Unknown")
                response_time = result.get("response_time", 0)
                print(f"{status} @{username:<15} | {proxy:<30} | IP: {ip:<15} | {response_time}s")
            else:
                error = result.get("error", "Unknown error")[:40]
                print(f"{status} @{username:<15} | {proxy:<30} | Error: {error}")
    
    def get_working_proxies(self, results: Dict[str, Dict]) -> Dict[str, str]:
        """Повертає тільки робочі проксі."""
        return {
            username: result["proxy"] 
            for username, result in results.items() 
            if result["working"]
        }


async def validate_project_proxies():
    """Перевіряє проксі з файлу проекту."""
    import os
    
    proxies_file = "proxies.json"
    if not os.path.exists(proxies_file):
        print(f"❌ Proxy file {proxies_file} not found!")
        return {}
    
    try:
        with open(proxies_file, 'r', encoding='utf-8') as f:
            proxies = json.load(f)
    except Exception as e:
        print(f"❌ Error loading proxies: {e}")
        return {}
    
    validator = ProxyValidator()
    results = await validator.test_all_proxies(proxies)
    validator.print_results(results)
    
    # Зберігаємо результати
    with open("proxy_test_results.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    working_proxies = validator.get_working_proxies(results)
    
    if working_proxies:
        print(f"\n🎉 {len(working_proxies)} proxies are working!")
        print("Results saved to proxy_test_results.json")
        
        # Оновлюємо proxies.json тільки робочими проксі
        with open("proxies_working.json", 'w', encoding='utf-8') as f:
            json.dump(working_proxies, f, indent=2, ensure_ascii=False)
        print("Working proxies saved to proxies_working.json")
    else:
        print("\n💥 No working proxies found!")
        print("⚠️ System will not work safely without proxies!")
    
    return working_proxies


async def main():
    """Main function."""
    print("🔍 Proxy Validation System")
    print("=" * 50)
    
    working_proxies = await validate_project_proxies()
    
    if not working_proxies:
        print("\n🚨 CRITICAL: No working proxies!")
        print("Please check your proxy configuration before running the automation.")
        return False
    
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        if not result:
            exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Validation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")