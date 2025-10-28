#!/usr/bin/env python3
"""
Main launcher script for Twitter/X Automation System

This script provides a unified interface to manage accounts and run the automation.
"""

import asyncio
import os
import sys
from typing import Optional

# Add current directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from twscrape import API
from twitter_automation import TwitterAutomation
from telegram_bot import TwitterTelegramBot, TwitterBotConfig


def load_env_file(file_path: str = "config.env"):
    """Load environment variables from .env and/or config.env if present.

    Precedence: .env (if exists) is loaded first, then config.env (if exists) fills any missing keys.
    """
    loaded_any = False

    def _load(path: str):
        nonlocal loaded_any
        try:
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Do not overwrite keys already set (allows .env to take precedence)
                        os.environ.setdefault(key.strip(), value.strip())
            print(f"✅ Завантажено конфіг з {path}")
            loaded_any = True
        except Exception as e:
            print(f"⚠️ Не вдалося завантажити {path}: {e}")

    # Prefer .env if present
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        _load(dotenv_path)

    # Backwards-compat: load config.env (relative to CWD or script dir)
    # Try explicit path param first
    if os.path.isabs(file_path) and os.path.exists(file_path):
        _load(file_path)
    else:
        # Try relative to script dir
        config_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(config_path):
            _load(config_path)
        else:
            # Finally, try CWD
            if os.path.exists(file_path):
                _load(file_path)

    if not loaded_any:
        print("ℹ️ Файл конфігурації .env або config.env не знайдено — використовую значення за замовчуванням.")


async def setup_accounts():
    """Setup and manage accounts."""
    print("🔧 Управління акаунтами")
    print("=" * 50)
    print()
    print("1. Додати всі акаунти зі скрипта")
    print("2. Показати статус акаунтів")
    print("3. Увійти в усі акаунти")
    print("4. Скинути блокування акаунтів")
    print("5. Видалити неактивні акаунти")
    print("6. Назад до головного меню")
    print()
    
    choice = input("Оберіть варіант (1-6): ").strip()
    
    if choice == "1":
        # Import and run bulk account setup
        from setup_accounts_bulk import add_all_accounts
        await add_all_accounts()
    
    elif choice == "2":
        from setup_accounts_bulk import show_accounts_status
        await show_accounts_status()
    
    elif choice == "3":
        api = API()
        print("🔄 Вхід в усі акаунти...")
        result = await api.pool.login_all()
        print(f"✅ Успішно: {result['success']}, ❌ Помилки: {result['failed']}")
    
    elif choice == "4":
        api = API()
        await api.pool.reset_locks()
        print("✅ Всі блокування акаунтів скинуто.")
    
    elif choice == "5":
        api = API()
        await api.pool.delete_inactive()
        print("✅ Всі неактивні акаунти видалено.")
    
    elif choice == "6":
        return
    
    else:
        print("❌ Невірний вибір.")
    
    input("\nНатисніть Enter щоб продовжити...")


async def test_automation():
    """Test the automation system."""
    print("🧪 Тестування системи автоматизації")
    print("=" * 50)
    print()
    
    api = API()
    automation = TwitterAutomation(api)
    
    # Get account status
    active_accounts = await automation.get_active_accounts()
    print(f"👥 Активні акаунти: {len(active_accounts)}")
    
    if not active_accounts:
        print("❌ Немає доступних активних акаунтів. Спочатку налаштуйте акаунти.")
        input("Натисніть Enter щоб продовжити...")
        return
    
    # Get test URL
    test_url = input("🔗 Введіть URL Twitter/X для тестування (або натисніть Enter для демо): ").strip()
    
    if not test_url:
        test_url = "https://x.com/elonmusk/status/1234567890"
        print(f"Використовуємо демо URL: {test_url}")
    
    print(f"\n🎯 Тестування автоматизації з: {test_url}")
    print("⏳ Це може зайняти кілька хвилин...")
    
    try:
        result = await automation.auto_engage_tweet(test_url)
        
        print("\n📊 Результати тестування:")
        print(f"ID твіта: {result.get('tweet_id', 'N/A')}")
        
        if "error" in result:
            print(f"❌ Помилка: {result['error']}")
        else:
            actions = result.get("actions", {})
            print(f"❤️ Лайки: {actions.get('likes', 0)}")
            print(f"🔄 Ретвіти: {actions.get('retweets', 0)}")
            print(f"👀 Перегляди: {actions.get('views', 0)}")
            
            if result.get("errors"):
                print(f"⚠️ Помилки: {len(result['errors'])}")
                
    except Exception as e:
        print(f"❌ Тест не вдався: {e}")
    
    input("\nНатисніть Enter щоб продовжити...")


def run_telegram_bot():
    """Run the Telegram bot."""
    print("🤖 Запуск Telegram бота")
    print("=" * 50)

    # Ensure env vars are loaded
    load_env_file()

    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not token:
            print("❌ TELEGRAM_BOT_TOKEN не налаштовано у .env або середовищі")
            print("💡 Додайте TELEGRAM_BOT_TOKEN у .env та спробуйте ще раз")
            input("\nНатисніть Enter щоб продовжити...")
            return

        config = TwitterBotConfig()
        bot = TwitterTelegramBot(config)
        bot.run()  # Blocking run (Ctrl+C to stop)
    except ModuleNotFoundError as e:
        print(f"❌ Не знайдено залежність: {e}")
        print("💡 Встановіть: pip install python-telegram-bot==20.7")
        input("\nНатисніть Enter щоб продовжити...")
    except KeyboardInterrupt:
        print("\n👋 Бота зупинено користувачем.")
    except Exception as e:
        print(f"❌ Помилка запуску Telegram бота: {e}")
        input("\nНатисніть Enter щоб продовжити...")


async def manual_process():
    """Manually process a tweet."""
    print("🎯 Ручна обробка твітів")
    print("=" * 50)
    print()
    
    api = API()
    automation = TwitterAutomation(api)
    
    # Get account status
    active_accounts = await automation.get_active_accounts()
    print(f"👥 Активні акаунти: {len(active_accounts)}")
    
    if not active_accounts:
        print("❌ Немає доступних активних акаунтів. Спочатку налаштуйте акаунти.")
        input("Натисніть Enter щоб продовжити...")
        return
    
    # Get tweet URL
    tweet_url = input("🔗 Введіть URL Twitter/X: ").strip()
    if not tweet_url:
        print("❌ URL не надано.")
        input("Натисніть Enter щоб продовжити...")
        return
    
    print()
    print("📊 Варіанти взаємодії:")
    print("1. Авто (реалістичні числа)")
    print("2. Власні числа")
    print("3. Висока активність")
    print("4. Низька активність")
    
    mode = input("\nОберіть режим (1-4): ").strip()
    
    try:
        if mode == "1":
            result = await automation.auto_engage_tweet(tweet_url)
        
        elif mode == "2":
            likes = int(input("❤️ Кількість лайків: ") or "0")
            retweets = 0  # ВИМКНЕНО: ретвіти повністю відключені
            views = int(input("👀 Кількість переглядів: ") or "0")
            print("⚠️ УВАГА: Ретвіти відключені в системі")
            result = await automation.process_tweet_url(tweet_url, likes, retweets, views)
        
        elif mode == "3":
            # High engagement - use more accounts
            total = len(active_accounts)
            likes = min(total, int(total * 0.6))
            retweets = 0  # ВИМКНЕНО: ретвіти повністю відключені
            views = min(total, int(total * 0.9))
            result = await automation.process_tweet_url(tweet_url, likes, retweets, views)
        
        elif mode == "4":
            # Low engagement
            total = len(active_accounts)
            likes = min(total, max(1, int(total * 0.1)))
            retweets = 0  # ВИМКНЕНО: ретвіти повністю відключені
            views = min(total, max(1, int(total * 0.3)))
            result = await automation.process_tweet_url(tweet_url, likes, retweets, views)
        
        else:
            print("❌ Невірний режим.")
            input("Натисніть Enter щоб продовжити...")
            return
        
        print("\n📊 Результати обробки:")
        if "error" in result:
            print(f"❌ Помилка: {result['error']}")
        else:
            actions = result.get("actions", {})
            print(f"✅ Успішно оброблено!")
            print(f"❤️ Лайки: {actions.get('likes', 0)}")
            print(f"🔄 Ретвіти: {actions.get('retweets', 0)}")
            print(f"👀 Перегляди: {actions.get('views', 0)}")
            
            if result.get("errors"):
                print(f"⚠️ Деякі дії не вдалися: {len(result['errors'])} помилок")
    
    except Exception as e:
        print(f"❌ Обробка не вдалася: {e}")
    
    input("\nНатисніть Enter щоб продовжити...")


def main_menu():
    """Display main menu and handle user choices."""
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
        
        print("🚀 Система автоматизації Twitter/X")
        print("=" * 50)
        print()
        print("1. 🔧 Управління акаунтами")
        print("2. 🌐 Перевірка проксі")
        print("3. 🤖 Запуск Telegram бота")
        print("4. 🎯 Ручна обробка твітів")
        print("5. 🧪 Тест автоматизації")
        print("6. 📊 Статус системи")
        print("7. ❌ Вихід")
        print()
        
        choice = input("Оберіть варіант (1-7): ").strip()
        
        if choice == "1":
            asyncio.run(setup_accounts())
        
        elif choice == "2":
            asyncio.run(validate_proxies())
        
        elif choice == "3":
            run_telegram_bot()
        
        elif choice == "4":
            asyncio.run(manual_process())
        
        elif choice == "5":
            asyncio.run(test_automation())
        
        elif choice == "6":
            asyncio.run(show_system_status())
        
        elif choice == "7":
            print("👋 До побачення!")
            break
        
        else:
            print("❌ Невірний вибір. Спробуйте ще раз.")
            input("Натисніть Enter щоб продовжити...")


async def validate_proxies():
    """Validate all configured proxies."""
    print("🌐 Перевірка проксі")
    print("=" * 50)
    
    try:
        from proxy_validator import validate_project_proxies
        working_proxies = await validate_project_proxies()
        
        if working_proxies:
            print(f"\n✅ Перевірка завершена! {len(working_proxies)} проксі працюють.")
            print("Система готова до безпечної автоматизації.")
        else:
            print(f"\n🚨 ПОПЕРЕДЖЕННЯ: Не знайдено робочих проксі!")
            print("Запуск автоматизації без проксі небезпечний і може призвести до блокування акаунтів.")
            
    except ImportError:
        print("❌ Валідатор проксі не знайдено. Перевірте файл proxy_validator.py.")
    except Exception as e:
        print(f"❌ Помилка під час перевірки проксі: {e}")
    
    input("\nНатисніть Enter щоб продовжити...")


async def show_system_status():
    """Show system status."""
    print("📊 Статус системи")
    print("=" * 50)
    
    try:
        api = API()
        
        # Account statistics
        stats = await api.pool.stats()
        print(f"📈 Статистика акаунтів:")
        print(f"• Загальна кількість акаунтів: {stats.get('total', 0)}")
        print(f"• Активні акаунти: {stats.get('active', 0)}")
        print(f"• Неактивні акаунти: {stats.get('inactive', 0)}")
        
        # Show locked queues
        locked_queues = [k for k in stats.keys() if k.startswith('locked_')]
        if locked_queues:
            print(f"\n🔒 Заблоковані черги:")
            for queue in locked_queues:
                count = stats[queue]
                queue_name = queue.replace('locked_', '')
                print(f"• {queue_name}: {count} акаунтів заблоковано")
        
        # Proxy status
        print(f"\n🌐 Статус проксі:")
        import os
        import json
        
        if os.path.exists("proxies_working.json"):
            try:
                with open("proxies_working.json", 'r') as f:
                    working_proxies = json.load(f)
                print(f"✅ Перевірені проксі: {len(working_proxies)}")
            except:
                print("❌ Помилка читання перевірених проксі")
        elif os.path.exists("proxies.json"):
            try:
                with open("proxies.json", 'r') as f:
                    proxies = json.load(f)
                print(f"⚠️ Неперевірені проксі: {len(proxies)}")
                print("💡 Запустіть 'python3 proxy_validator.py' для перевірки проксі")
            except:
                print("❌ Помилка читання конфігурації проксі")
        else:
            print("🚨 Конфігурація проксі не знайдена - НЕБЕЗПЕЧНО!")
        
        # Configuration status
        print(f"\n⚙️ Конфігурація:")
        print(f"• Telegram токен: {'✅ Встановлено' if os.getenv('TELEGRAM_BOT_TOKEN') else '❌ Не встановлено'}")
        print(f"• Авто режим: {'✅ Увімкнено' if os.getenv('AUTO_MODE', 'true').lower() == 'true' else '❌ Вимкнено'}")
        print(f"• Режим налагодження: {'✅ Увімкнено' if os.getenv('DEBUG_MODE', 'false').lower() == 'true' else '❌ Вимкнено'}")
        
    except Exception as e:
        print(f"❌ Помилка отримання статусу: {e}")
    
    input("\nНатисніть Enter щоб продовжити...")


def main():
    """Main function."""
    # Load configuration
    load_env_file()
    
    # Show welcome message
    print("🚀 Ласкаво просимо до системи автоматизації Twitter/X!")
    print()
    print("Ця система дозволяє вам:")
    print("• Керувати кількома акаунтами Twitter/X")
    print("• Автоматично лайкати, ретвітити та переглядати пости")
    print("• Інтегруватися з Telegram для легкої автоматизації")
    print("• Обробляти твіти з реалістичними паттернами взаємодії")
    print()
    
    # Check if we have any accounts
    try:
        api = API()
        accounts_info = asyncio.run(api.pool.accounts_info())
        
        if not accounts_info:
            print("ℹ️ Акаунти не знайдено. Давайте спочатку їх налаштуємо!")
            input("Натисніть Enter щоб перейти до налаштування акаунтів...")
            asyncio.run(setup_accounts())
        else:
            active_count = sum(1 for acc in accounts_info if acc["active"])
            print(f"✅ Знайдено {len(accounts_info)} акаунтів ({active_count} активних)")
    
    except Exception as e:
        print(f"⚠️ Не вдалося перевірити акаунти: {e}")
    
    # Start main menu
    main_menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 System stopped by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check your configuration and try again.")