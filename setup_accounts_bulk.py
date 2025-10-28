#!/usr/bin/env python3
"""
Bulk Account Setup - Add multiple accounts quickly

This script adds all your Twitter/X accounts from the provided data.
"""

import asyncio
from twscrape import API


def load_accounts_data():
    """Load account data from secure JSON file."""
    import json
    import os
    
    accounts_file = "accounts.json"
    if not os.path.exists(accounts_file):
        print(f"❌ Файл даних акаунтів {accounts_file} не знайдено!")
        print("Будь ласка, створіть accounts.json з даними ваших акаунтів.")
        return []
    
    try:
        with open(accounts_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Помилка завантаження даних акаунтів: {e}")
        return []


async def add_all_accounts():
    """Add all accounts to the system."""
    print("🚀 Масове налаштування акаунтів")
    print("=" * 50)
    
    # Load accounts from secure file
    accounts_data = load_accounts_data()
    if not accounts_data:
        return
    
    print(f"Додавання {len(accounts_data)} акаунтів...")
    print()
    
    api = API()
    success_count = 0
    failed_count = 0
    
    # Load proxy assignments
    import json
    import os
    
    proxy_file = "proxies.json"
    proxies = {}
    if os.path.exists(proxy_file):
        try:
            with open(proxy_file, 'r', encoding='utf-8') as f:
                proxies = json.load(f)
            print(f"✅ Завантажено {len(proxies)} призначень проксі")
        except Exception as e:
            print(f"⚠️ Помилка завантаження проксі: {e}")
    else:
        print("⚠️ Конфігурацію проксі не знайдено!")
    
    for i, account_data in enumerate(accounts_data, 1):
        username = account_data["login"]
        password = account_data["password"]
        email = account_data["mail"]
        ct0 = account_data["ct0"]
        auth_token = account_data["auth_token"]
        
        # Get proxy for this account - assign sequentially
        proxy_list = list(proxies.values()) if proxies else []
        account_proxy = proxy_list[(i-1) % len(proxy_list)] if proxy_list else None
        
        # Build cookies string
        cookies = f"auth_token={auth_token}; ct0={ct0}"
        
        proxy_info = f" with proxy {account_proxy[:30]}..." if account_proxy else " WITHOUT PROXY (DANGEROUS!)"
        print(f"[{i}/{len(accounts_data)}] Додавання акаунту: @{username}{proxy_info}")
        
        try:
            await api.pool.add_account(
                username=username,
                password=password,
                email=email,
                email_password="dummy_email_pass",  # Using dummy since we have tokens
                cookies=cookies,
                proxy=account_proxy  # КРИТИЧНО: додаємо проксі!
            )
            print(f"✅ Успішно додано @{username}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Не вдалося додати @{username}: {e}")
            failed_count += 1
        
        print()
    
    print("=" * 50)
    print(f"📊 Підсумок:")
    print(f"✅ Успішно додано: {success_count}")
    print(f"❌ Помилок: {failed_count}")
    print(f"📈 Всього: {len(accounts_data)}")
    
    if success_count > 0:
        print(f"\n🎉 Чудово! У вас є {success_count} акаунтів готових для автоматизації!")
        
        # Show accounts status
        accounts_info = await api.pool.accounts_info()
        print(f"\n📋 Статус акаунтів:")
        for info in accounts_info:
            status = "🟢 Active" if info["active"] else "🔴 Inactive"
            print(f"  @{info['username']}: {status}")


async def show_accounts_status():
    """Show status of all accounts."""
    print("📋 Current Accounts Status")
    print("=" * 50)
    
    api = API()
    accounts_info = await api.pool.accounts_info()
    
    if not accounts_info:
        print("❌ No accounts found in the system.")
        return
    
    active_count = sum(1 for acc in accounts_info if acc["active"])
    inactive_count = len(accounts_info) - active_count
    
    print(f"Total accounts: {len(accounts_info)}")
    print(f"🟢 Active: {active_count}")
    print(f"🔴 Inactive: {inactive_count}")
    print()
    
    for info in accounts_info:
        status = "🟢 Active" if info["active"] else "🔴 Inactive"
        req_count = info["total_req"]
        last_used = info["last_used"].strftime("%Y-%m-%d %H:%M") if info["last_used"] else "Never"
        
        print(f"@{info['username']:<20} {status:<12} Requests: {req_count:<5} Last used: {last_used}")


async def main():
    """Main function."""
    print("Welcome to Bulk Account Setup!")
    print()
    print("Options:")
    print("1. Add all accounts to system")
    print("2. Show current accounts status")
    print()
    
    choice = input("Enter your choice (1-2): ").strip()
    print()
    
    if choice == "1":
        await add_all_accounts()
    elif choice == "2":
        await show_accounts_status()
    else:
        print("❌ Invalid choice. Please run again and select 1 or 2.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")