#!/usr/bin/env python3
"""
Quick Account Setup - Add account with just auth_token

This is a simplified script to quickly add a Twitter/X account using just the auth_token.
Perfect for when you have cookies and don't want to fill all the fields.

Usage:
    python quick_add_account.py
"""

import asyncio
import getpass
from twscrape import API


async def quick_add_account():
    """Quick account setup with minimal requirements."""
    print("🚀 Швидке налаштування акаунту Twitter/X")
    print("=" * 40)
    print()
    print("Цей скрипт швидко додасть ваш акаунт використовуючи cookies/auth_token.")
    print("Вам потрібно лише: ім'я користувача, auth_token (і опціонально ct0)")
    print()
    
    # Get username
    username = input("📝 Username (without @): ").strip()
    if not username:
        print("❌ Ім'я користувача є обов'язковим")
        return False
    
    # Get auth_token
    print("\n🔑 Отримання auth_token:")
    print("1. Перейдіть на https://x.com у вашому браузері (увійшовши в систему)")
    print("2. Відкрийте Інструменти розробника (F12)")
    print("3. Перейдіть до Application/Storage > Cookies > https://x.com")
    print("4. Знайдіть 'auth_token' і скопіюйте його значення")
    print()
    
    auth_token = getpass.getpass("🔐 Enter auth_token: ").strip()
    if not auth_token:
        print("❌ auth_token є обов'язковим")
        return False
    
    # Get ct0 (optional but recommended)
    ct0 = getpass.getpass("🔐 Enter ct0 (optional, press Enter to skip): ").strip()
    
    # Build cookies string
    if ct0:
        cookies = f"auth_token={auth_token}; ct0={ct0}"
    else:
        cookies = f"auth_token={auth_token}"
    
    print(f"\n🍪 Cookies підготовлено: auth_token=***...{auth_token[-4:]} {'+ ct0=***...' + ct0[-4:] if ct0 else ''}")
    
    # Add account
    try:
        api = API()
        
        # Use dummy values for required but unused fields when using cookies
        dummy_password = "dummy_pass"
        dummy_email = f"{username}@dummy.com"
        dummy_email_pass = "dummy_email_pass"
        
        await api.pool.add_account(
            username=username,
            password=dummy_password,
            email=dummy_email,
            email_password=dummy_email_pass,
            cookies=cookies
        )
        
        print(f"✅ Акаунт @{username} успішно додано!")
        print("💡 Тепер ви можете використовувати скрипт витягування даних!")
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка додавання акаунту: {e}")
        return False


async def main():
    """Main function."""
    print("Ласкаво просимо до швидкого налаштування акаунту!")
    print()
    
    success = await quick_add_account()
    
    if success:
        print("\n🎉 Налаштування завершено!")
        print("\n📋 Next steps:")
        print("1. Test your setup: python setup_accounts.py (option 4 - Show account status)")
        print("2. Extract tweet data: python extract_post_data.py <tweet_url>")
    else:
        print("\n❌ Setup failed. Please try again.")
    
    print("\n👋 Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
