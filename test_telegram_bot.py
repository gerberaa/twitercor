#!/usr/bin/env python3
"""
Тест Telegram бота з підтримкою гілок
"""
import asyncio
import os
from telegram_bot import TwitterBot

async def test_bot():
    """Тестування налаштувань бота"""
    
    # Завантажуємо змінні середовища
    from dotenv import load_dotenv
    load_dotenv()
    
    print("🤖 Тестування Telegram бота")
    print("=" * 50)
    
    # Перевіряємо основні налаштування
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID")
    thread_id = os.getenv("TELEGRAM_THREAD_ID")
    read_mode = os.getenv("TELEGRAM_READ_MODE")
    admin_id = os.getenv("ADMIN_USER_ID")
    
    print(f"📱 Bot Token: {'✅ Налаштовано' if bot_token else '❌ Відсутній'}")
    print(f"📢 Channel ID: {channel_id if channel_id else '❌ Не налаштовано'}")
    print(f"🧵 Thread ID: {thread_id if thread_id else '❌ Не налаштовано'}")
    print(f"📖 Read Mode: {read_mode}")
    print(f"👤 Admin ID: {admin_id if admin_id else '❌ Не налаштовано'}")
    print()
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN не налаштовано!")
        return
        
    try:
        # Створюємо бота
        bot = TwitterBot()
        print("✅ Бот створено успішно")
        
        # Перевіряємо підключення до Twitter API
        try:
            accounts = await bot.api.pool.accounts_info()
            print(f"✅ Twitter API: {len(accounts)} акаунтів доступно")
        except Exception as e:
            print(f"⚠️ Twitter API: {e}")
        
        print()
        print("🚀 Для запуску бота виконайте:")
        print("python3 telegram_bot.py")
        print()
        print("📋 Доступні команди в Telegram:")
        print("• /start - Показати привітання")
        print("• /channel - Перевірити налаштування каналу")
        print("• /status - Статус бота та акаунтів")
        print("• /auto on/off - Увімкнути/вимкнути авто-режим")
        
    except Exception as e:
        print(f"❌ Помилка створення бота: {e}")

if __name__ == "__main__":
    asyncio.run(test_bot())