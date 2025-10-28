#!/usr/bin/env python3
"""
Telegram Bot for Twitter/X Automation

This bot listens to messages in Telegram groups and automatically
processes Twitter/X links with likes, retweets, and views.
"""

import asyncio
import json
import logging
import os
import re
from typing import Dict, List, Optional

from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

from twscrape import API
from twitter_automation import TwitterAutomation


# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TwitterBotConfig:
    """Configuration for the Twitter automation bot."""
    
    def __init__(self):
        # Telegram settings
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        # Parse allowed lists (empty -> []) and strip spaces
        def _parse_csv_env(name: str) -> list[str]:
            raw = os.getenv(name, "")
            parts = [p.strip() for p in raw.split(",") if p.strip()]
            return parts

        self.allowed_groups = _parse_csv_env("ALLOWED_GROUPS")
        self.allowed_users = _parse_csv_env("ALLOWED_USERS")
        
        # Channel/Thread settings
        self.telegram_channel_id = os.getenv("TELEGRAM_CHANNEL_ID", "")
        self.telegram_thread_id = os.getenv("TELEGRAM_THREAD_ID", "")
        self.telegram_read_mode = os.getenv("TELEGRAM_READ_MODE", "all")  # all, thread, replies
        self.admin_user_id = os.getenv("ADMIN_USER_ID", "")
        
        # Automation settings
        self.auto_mode = os.getenv("AUTO_MODE", "true").lower() == "true"
        self.min_delay = int(os.getenv("MIN_DELAY", "60"))  # Minimum delay between processing tweets
        self.max_delay = int(os.getenv("MAX_DELAY", "300"))  # Maximum delay
        
        # Engagement settings
        self.default_likes_min = int(os.getenv("DEFAULT_LIKES_MIN", "5"))
        self.default_likes_max = int(os.getenv("DEFAULT_LIKES_MAX", "15"))
    # Retweets are globally controllable via ENABLE_RETWEETS (default: false)
        self.enable_retweets = os.getenv("ENABLE_RETWEETS", "false").lower() == "true"
        self.default_retweets_min = int(os.getenv("DEFAULT_RETWEETS_MIN", "0"))
        self.default_retweets_max = int(os.getenv("DEFAULT_RETWEETS_MAX", "0"))
        self.default_views_min = int(os.getenv("DEFAULT_VIEWS_MIN", "20"))
        self.default_views_max = int(os.getenv("DEFAULT_VIEWS_MAX", "50"))


class TwitterTelegramBot:
    """Main Telegram bot class for Twitter automation."""
    
    def __init__(self, config: TwitterBotConfig):
        self.config = config
        self.api = API()
        self.automation = TwitterAutomation(self.api)
        self.processed_tweets = set()  # Track processed tweets to avoid duplicates
        self.last_processing_time = 0

        self.tweet_queue = asyncio.Queue()
        self.queue_worker_started = False
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        if not self.is_authorized(user_id, chat_id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        welcome_text = """
🤖 **Twitter/X Automation Bot**

I automatically process Twitter/X links posted in this group!

**Commands:**
• `/start` - Show this message
• `/status` - Show bot and accounts status
• `/stats` - Show processing statistics
• `/process <url>` - Manually process a tweet
• `/auto on/off` - Toggle auto-processing mode
• `/channel` - Show channel/thread settings

**Auto Mode:** {}

When auto mode is ON, I'll automatically process any Twitter/X links posted in the group with realistic engagement numbers.

Drop a Twitter/X link and watch the magic happen! ✨
        """.format("🟢 ON" if self.config.auto_mode else "🔴 OFF")
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown')

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        if not self.is_authorized(user_id, chat_id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        # Get account status
        active_accounts = await self.automation.get_active_accounts()
        accounts_info = await self.api.pool.accounts_info()
        
        total_accounts = len(accounts_info)
        active_count = len(active_accounts)
        inactive_count = total_accounts - active_count

        # Запускаємо воркер якщо ще не запущено
        if not self.queue_worker_started:
            asyncio.create_task(self.queue_worker())
            self.queue_worker_started = True
        
        status_text = f"""
📊 **Bot Status**

**Accounts:**
• Total: {total_accounts}
• 🟢 Active: {active_count}
• 🔴 Inactive: {inactive_count}

**Settings:**
• Auto Mode: {"🟢 ON" if self.config.auto_mode else "🔴 OFF"}
• Processed Tweets: {len(self.processed_tweets)}

**Active Accounts:**
        """
        
        if active_accounts:
            for account in active_accounts[:10]:  # Show first 10
                status_text += f"• @{account}\n"
            if len(active_accounts) > 10:
                status_text += f"• ... and {len(active_accounts) - 10} more\n"
        else:
            status_text += "• None\n"
        
        await update.message.reply_text(status_text, parse_mode='Markdown')

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command."""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        if not self.is_authorized(user_id, chat_id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return

        stats_text = f"""
📈 **Processing Statistics**

• Processed Tweets: {len(self.processed_tweets)}
• Auto Mode: {"🟢 ON" if self.config.auto_mode else "🔴 OFF"}

**Recent Tweets:**
        """
        
        recent_tweets = list(self.processed_tweets)[-5:]  # Last 5
        if recent_tweets:
            for tweet_id in recent_tweets:
                stats_text += f"• {tweet_id}\n"
        else:
            stats_text += "• None processed yet\n"
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')

    async def process_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /process command."""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        if not self.is_authorized(user_id, chat_id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Please provide a Twitter/X URL. Usage: `/process <url>`", parse_mode='Markdown')
            return
        
        tweet_url = context.args[0]
        await self.process_tweet_from_message(update, tweet_url, manual=True)

    async def auto_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /auto command."""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        if not self.is_authorized(user_id, chat_id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        if not context.args or context.args[0].lower() not in ['on', 'off']:
            await update.message.reply_text("❌ Usage: `/auto on` or `/auto off`", parse_mode='Markdown')
            return
        
        new_mode = context.args[0].lower() == 'on'
        self.config.auto_mode = new_mode
        
        mode_text = "🟢 ON" if new_mode else "🔴 OFF"
        await update.message.reply_text(f"✅ Auto mode set to: {mode_text}")

    async def channel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /channel command - показує налаштування каналу та гілки."""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        if not self.is_authorized(user_id, chat_id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        current_chat = update.effective_chat
        current_message = update.message
        
        channel_text = f"""
🔧 **Налаштування каналу/гілки**

**Поточний чат:**
• ID: `{chat_id}`
• Тип: {current_chat.type}
• Назва: {current_chat.title if current_chat.title else "Немає"}

**Налаштування бота:**
• Цільовий канал: `{self.config.telegram_channel_id if self.config.telegram_channel_id else "Не налаштовано"}`
• ID гілки: `{self.config.telegram_thread_id if self.config.telegram_thread_id else "Немає"}`
• Режим читання: `{self.config.telegram_read_mode}`

**Поточне повідомлення:**
• Message ID: `{current_message.message_id}`
• Reply to: `{current_message.reply_to_message.message_id if current_message.reply_to_message else "Немає"}`

**Чи буде це повідомлення оброблено?**
{"✅ ТАК" if self.is_message_from_target_source(update) else "❌ НІ"}

**Для налаштування:**
1. Скопіюйте ID поточного чату в .env файл як TELEGRAM_CHANNEL_ID
2. Якщо потрібна конкретна гілка - скопіюйте Message ID як TELEGRAM_THREAD_ID
3. Встановіть TELEGRAM_READ_MODE: all/thread/replies
        """
        
        await update.message.reply_text(channel_text, parse_mode='Markdown')

    def is_authorized(self, user_id: int, chat_id: int) -> bool:
        """Check if user/group is authorized to use the bot."""
        # Check if it's an allowed group
        if str(chat_id) in self.config.allowed_groups:
            return True
        
        # Check if it's an allowed user
        if str(user_id) in self.config.allowed_users:
            return True
        
        # If no restrictions are set, allow all
        if not self.config.allowed_groups and not self.config.allowed_users:
            return True
        
        return False

    def extract_twitter_urls(self, text: str) -> List[str]:
        """Extract Twitter/X URLs from text."""
        patterns = [
            r'https?://(?:www\.)?(?:twitter\.com|x\.com)/\w+/status/\d+',
            r'https?://(?:www\.)?(?:twitter\.com|x\.com)/i/status/\d+',
        ]
        
        urls = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            urls.extend(matches)
        
        return list(set(urls))  # Remove duplicates

    def is_message_from_target_source(self, update: Update) -> bool:
        """Перевіряє чи повідомлення надійшло з цільового джерела (каналу/гілки)."""
        chat_id = update.effective_chat.id
        message = update.message
        
        # Якщо не налаштований канал, приймаємо всі повідомлення
        if not self.config.telegram_channel_id:
            return True
            
        # Перевіряємо чи повідомлення з правильного каналу
        target_channel_id = int(self.config.telegram_channel_id)
        if chat_id != target_channel_id:
            logger.debug(f"Повідомлення не з цільового каналу. Поточний: {chat_id}, Цільовий: {target_channel_id}")
            return False
        
        # Перевіряємо режим читання
        if self.config.telegram_read_mode == "all":
            return True
        elif self.config.telegram_read_mode == "thread":
            # Перевіряємо чи повідомлення з конкретної гілки
            if not self.config.telegram_thread_id:
                return True
            
            target_thread_id = int(self.config.telegram_thread_id)
            
            # Перевіряємо чи це відповідь на цільове повідомлення
            if message.reply_to_message and message.reply_to_message.message_id == target_thread_id:
                return True
            # Або чи це саме цільове повідомлення
            elif message.message_id == target_thread_id:
                return True
            else:
                logger.debug(f"Повідомлення не з цільової гілки. Message ID: {message.message_id}, Target: {target_thread_id}")
                return False
        elif self.config.telegram_read_mode == "replies":
            # Читаємо лише прямі відповіді на цільове повідомлення
            if not self.config.telegram_thread_id:
                return True
                
            target_thread_id = int(self.config.telegram_thread_id)
            if message.reply_to_message and message.reply_to_message.message_id == target_thread_id:
                return True
            else:
                return False
        
        return True

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages and process Twitter links."""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Перевіряємо чи повідомлення з правильного каналу
        if not self.is_message_from_target_source(update):
            return
        
        if not self.is_authorized(user_id, chat_id):
            return
        
        if not self.config.auto_mode:
            return
        
        message_text = update.message.text or ""
        twitter_urls = self.extract_twitter_urls(message_text)
        
        if not twitter_urls:
            return
        
        for url in twitter_urls:
            # Notify user that the link is queued for processing
            await update.message.reply_text(f"🔔 Посилання додано в чергу на накрутку: {url}")
            await self.process_tweet_from_message(update, url, manual=False)

    async def process_tweet_from_message(self, update: Update, tweet_url: str, manual: bool = False):
        """Process a tweet URL from a message."""
        try:
            # Extract tweet ID
            tweet_id = self.automation.interaction_api.extract_tweet_id(tweet_url)
            if not tweet_id:
                if manual:
                    await update.message.reply_text("❌ Invalid Twitter/X URL")
                return
            
            # Check if already processed
            if tweet_id in self.processed_tweets:
                if manual:
                    await update.message.reply_text("ℹ️ This tweet has already been processed")
                return
            
            # Add random delay for natural behavior (only for auto mode)
            if not manual and len(self.processed_tweets) > 0:
                import random
                delay = random.randint(self.config.min_delay, self.config.max_delay)
                logger.info(f"Waiting {delay} seconds before processing tweet {tweet_id}")
                await asyncio.sleep(delay)
            
            # Send processing message
            processing_msg = await update.message.reply_text(f"🔄 Processing tweet: {tweet_url}")
            
            # Process the tweet
            if manual:
                # For manual processing, use auto-engage (realistic numbers)
                result = await self.automation.auto_engage_tweet(tweet_url)
            else:
                # For auto mode, use custom ranges
                import random
                likes = random.randint(self.config.default_likes_min, self.config.default_likes_max)
                # Respect global retweet disable flag
                if self.config.enable_retweets:
                    retweets = random.randint(self.config.default_retweets_min, self.config.default_retweets_max)
                else:
                    retweets = 0
                views = random.randint(self.config.default_views_min, self.config.default_views_max)
                
                result = await self.automation.process_tweet_url(tweet_url, likes, retweets, views)
            
            # Add to processed list
            self.processed_tweets.add(tweet_id)
            
            # Send result message
            if "error" in result:
                await processing_msg.edit_text(f"❌ Error: {result['error']}")
            else:
                actions = result.get("actions", {})
                # Build actions section conditionally (hide retweets if disabled)
                actions_lines = [
                    "✅ **Tweet Processed Successfully!**",
                    "",
                    f"🎯 **Tweet:** {tweet_url}",
                    "",
                    "📊 **Actions Performed:",
                    f"• ❤️ Likes: {actions.get('likes', 0)}",
                ]
                if self.config.enable_retweets:
                    actions_lines.append(f"• 🔄 Retweets: {actions.get('retweets', 0)}")
                actions_lines.append(f"• 👀 Views: {actions.get('views', 0)}")
                actions_lines.append("")
                success_text = "\n".join(actions_lines)
                
                if result.get("final_stats"):
                    stats = result["final_stats"]
                    stats_lines = [
                        "**Current Stats:**",
                        f"• ❤️ Total Likes: {stats.get('likes', 0)}",
                    ]
                    if self.config.enable_retweets:
                        stats_lines.append(f"• 🔄 Total Retweets: {stats.get('retweets', 0)}")
                    stats_lines.extend([
                        f"• 💬 Replies: {stats.get('replies', 0)}",
                        f"• 👀 Views: {stats.get('views', 0)}",
                    ])
                    success_text += "\n" + "\n".join(stats_lines)
                
                if result.get("errors"):
                    success_text += f"\n⚠️ Some actions failed: {len(result['errors'])} errors"
                
                await processing_msg.edit_text(success_text, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Error processing tweet {tweet_url}: {e}")
            if 'processing_msg' in locals():
                await processing_msg.edit_text(f"❌ Error processing tweet: {str(e)}")
            else:
                await update.message.reply_text(f"❌ Error processing tweet: {str(e)}")

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        logger.error(f"Update {update} caused error {context.error}")

    def run(self):
        """Run the Telegram bot."""
        if not self.config.telegram_bot_token:
            print("❌ TELEGRAM_BOT_TOKEN environment variable is required!")
            print("Set it with: export TELEGRAM_BOT_TOKEN='your_bot_token_here'")
            return
        
        # Ensure an event loop exists for the current thread (Python 3.12 safety)
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        print("🚀 Starting Twitter/X Automation Telegram Bot...")
        print(f"🤖 Auto mode: {'ON' if self.config.auto_mode else 'OFF'}")
        print(f"🔧 Allowed groups: {self.config.allowed_groups if self.config.allowed_groups else 'All'}")
        print(f"👥 Allowed users: {self.config.allowed_users if self.config.allowed_users else 'All'}")
        
        # Create application
        application = Application.builder().token(self.config.telegram_bot_token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("status", self.status_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        application.add_handler(CommandHandler("process", self.process_command))
        application.add_handler(CommandHandler("auto", self.auto_command))
        application.add_handler(CommandHandler("channel", self.channel_command))
        
        # Message handler for auto-processing
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Error handler
        application.add_error_handler(self.error_handler)
        
        # Run the bot
        print("✅ Bot is running! Send /start to begin.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


async def test_automation():
    """Test function for automation without Telegram."""
    print("🧪 Testing Twitter automation...")
    
    api = API()
    automation = TwitterAutomation(api)
    
    # Test URL (replace with actual tweet URL)
    test_url = "https://x.com/elonmusk/status/1234567890"
    
    print(f"Testing with URL: {test_url}")
    result = await automation.auto_engage_tweet(test_url)
    
    print("Test result:")
    print(json.dumps(result, indent=2, default=str))


def main():
    """Main function."""
    config = TwitterBotConfig()
    bot = TwitterTelegramBot(config)
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user.")
    except Exception as e:
        print(f"❌ Bot error: {e}")


if __name__ == "__main__":
    # Check if we want to run tests
    import sys
    if "--test" in sys.argv:
        asyncio.run(test_automation())
    else:
        main()