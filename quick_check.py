#!/usr/bin/env python3
"""
Quick Account Check

Fast check to see if your Twitter/X account is working.

Usage:
    python quick_check.py
"""

import asyncio
import sys
from twscrape import API


async def quick_test():
    """Quick test of account functionality."""
    print("⚡ Швидка перевірка акаунту")
    print("=" * 30)
    
    api = API()
    
    # Check if we have accounts
    try:
        accounts = await api.pool.accounts_info()
        
        if not accounts:
            print("❌ Акаунти не знайдено!")
            print("💡 Спочатку додайте акаунт: python quick_add_account.py")
            return False
        
        active_accounts = [acc for acc in accounts if acc.get('active', False)]
        
        if not active_accounts:
            print("❌ Активні акаунти не знайдено!")
            print("💡 Перевірте статус акаунту: python check_account.py")
            return False
        
        print(f"✅ Знайдено {len(active_accounts)} активних акаунтів")
        
        # Test with first active account
        print("🔍 Тестування доступу до API...")
        
        user = await api.user_by_login("elonmusk")  # Use Elon Musk as test (more reliable)
        
        if user:
            print(f"✅ API працює! Успішно отримано дані @{user.username}")
            print(f"   👥 Підписників: {user.followersCount:,}")
            print(f"   📝 Твітів: {user.statusesCount:,}")
            return True
        else:
            print("❌ Тест API не вдався - не вдалося отримати дані користувача")
            return False
            
    except Exception as e:
        print(f"❌ Помилка: {str(e)}")
        
        # Suggest solutions based on error
        error_str = str(e).lower()
        if "unauthorized" in error_str or "token" in error_str:
            print("💡 Рішення: Ваші cookies можуть бути застарілими. Спробуйте знову додати акаунт.")
        elif "rate" in error_str:
            print("💡 Рішення: Обмеження швидкості. Зачекайте 15 хвилин і спробуйте знову.")
        elif "account" in error_str:
            print("💡 Рішення: Спочатку додайте акаунт: python quick_add_account.py")
        else:
            print("💡 Рішення: Запустіть повну перевірку: python check_account.py")
        
        return False


async def main():
    """Main function."""
    success = await quick_test()
    
    if success:
        print("\n🎉 Акаунт працює!")
        print("🚀 Готовий до витягування даних твітів!")
        print("\n📝 Використання: python extract_post_data.py <tweet_url>")
    else:
        print("\n❌ Перевірка акаунту не вдалася!")
        print("🔧 Run detailed check: python check_account.py")
    
    return success


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Check cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
