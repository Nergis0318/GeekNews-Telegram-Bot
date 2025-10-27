import asyncio
import logging
import sqlite3

import feedparser
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import re
import os

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database setup
DB_PATH = os.getenv("DB_PATH", "bot.db")
BOT_TOKEN = os.getenv("BOT_TOKEN")


def init_db():
    """Initialize the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            chat_id INTEGER PRIMARY KEY,
            subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sent_articles (
            article_id INTEGER PRIMARY KEY,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def add_subscriber(chat_id: int) -> tuple[bool, bool]:
    """Add a subscriber to the database.

    Returns:
        tuple: (success, already_subscribed)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if already subscribed
        cursor.execute("SELECT 1 FROM subscribers WHERE chat_id = ?", (chat_id,))
        already_subscribed = cursor.fetchone() is not None

        if not already_subscribed:
            cursor.execute("INSERT INTO subscribers (chat_id) VALUES (?)", (chat_id,))
            conn.commit()

        conn.close()
        return True, already_subscribed
    except Exception as e:
        logger.error(f"Error adding subscriber {chat_id}: {e}")
        return False, False


def remove_subscriber(chat_id: int) -> tuple[bool, bool]:
    """Remove a subscriber from the database.

    Returns:
        tuple: (success, was_subscribed)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if user was subscribed
        cursor.execute("SELECT 1 FROM subscribers WHERE chat_id = ?", (chat_id,))
        was_subscribed = cursor.fetchone() is not None

        cursor.execute("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,))
        conn.commit()
        conn.close()
        return True, was_subscribed
    except Exception as e:
        logger.error(f"Error removing subscriber {chat_id}: {e}")
        return False, False


def get_subscribers():
    """Get all subscribers from the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id FROM subscribers")
        subscribers = [row[0] for row in cursor.fetchall()]
        conn.close()
        return subscribers
    except Exception as e:
        logger.error(f"Error getting subscribers: {e}")
        return []


def is_article_sent(article_id: str) -> bool:
    """Check if an article has been sent already."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM sent_articles WHERE article_id = ?", (article_id,)
        )
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        logger.error(f"Error checking article {article_id}: {e}")
        return False


def mark_article_sent(article_id: str):
    """Mark an article as sent."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO sent_articles (article_id) VALUES (?)", (article_id,)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error marking article {article_id} as sent: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - subscribe user, group, or channel."""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    chat_title = (
        update.effective_chat.title
        if chat_type in ["group", "supergroup", "channel"]
        else None
    )

    success, already_subscribed = add_subscriber(chat_id)

    if not success:
        await update.message.reply_text(
            "❌ 구독 처리 중 오류가 발생했습니다. 다시 시도해주세요."
        )
        return

    # Different messages based on chat type
    if chat_type in ["group", "supergroup"]:
        chat_name = f"그룹 '{chat_title}'" if chat_title else "이 그룹"
        if already_subscribed:
            await update.message.reply_text(
                f"ℹ️ {chat_name}은 이미 GeekNews를 구독하고 있습니다!\n"
                "새로운 기사가 올라오면 계속 알림을 받으실 수 있습니다."
            )
            logger.info(
                f"Already subscribed group tried to subscribe again: {chat_id} ({chat_title})"
            )
        else:
            await update.message.reply_text(
                f"✅ {chat_name}에서 GeekNews 구독을 시작했습니다!\n"
                "새로운 기사가 올라오면 이 그룹에 알림을 보내드립니다."
            )
            logger.info(f"New group subscriber: {chat_id} ({chat_title})")
    elif chat_type == "channel":
        chat_name = f"채널 '{chat_title}'" if chat_title else "이 채널"
        if already_subscribed:
            logger.info(
                f"Already subscribed channel tried to subscribe again: {chat_id} ({chat_title})"
            )
        else:
            logger.info(f"New channel subscriber: {chat_id} ({chat_title})")
        # For channels, the message is sent to the channel itself
    else:
        # Private chat
        if already_subscribed:
            await update.message.reply_text(
                "ℹ️ 이미 GeekNews를 구독하고 계십니다!\n"
                "새로운 기사가 올라오면 계속 알림을 받으실 수 있습니다."
            )
            logger.info(f"Already subscribed user tried to subscribe again: {chat_id}")
        else:
            await update.message.reply_text(
                "✅ GeekNews 구독을 시작했습니다!\n"
                "새로운 기사가 올라오면 알림을 받으실 수 있습니다."
            )
            logger.info(f"New subscriber: {chat_id}")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command - unsubscribe user, group, or channel."""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    chat_title = (
        update.effective_chat.title
        if chat_type in ["group", "supergroup", "channel"]
        else None
    )

    success, was_subscribed = remove_subscriber(chat_id)

    if not success:
        await update.message.reply_text("❌ 구독 해제 중 오류가 발생했습니다.")
        return

    # Different messages based on chat type
    if chat_type in ["group", "supergroup"]:
        chat_name = f"그룹 '{chat_title}'" if chat_title else "이 그룹"
        if was_subscribed:
            await update.message.reply_text(
                f"👋 {chat_name}의 GeekNews 구독을 해제했습니다.\n"
                "다시 구독하시려면 /start 명령을 사용해주세요."
            )
            logger.info(f"Unsubscribed group: {chat_id} ({chat_title})")
        else:
            await update.message.reply_text(
                f"ℹ️ {chat_name}은 이미 구독이 해제되어 있습니다.\n"
                "구독을 시작하시려면 /start 명령을 사용해주세요."
            )
            logger.info(
                f"Already unsubscribed group tried to unsubscribe: {chat_id} ({chat_title})"
            )
    elif chat_type == "channel":
        if was_subscribed:
            logger.info(f"Unsubscribed channel: {chat_id} ({chat_title})")
        else:
            logger.info(
                f"Already unsubscribed channel tried to unsubscribe: {chat_id} ({chat_title})"
            )
    else:
        # Private chat
        if was_subscribed:
            await update.message.reply_text(
                "👋 GeekNews 구독을 해제했습니다.\n"
                "다시 구독하시려면 /start 명령을 사용해주세요."
            )
            logger.info(f"Unsubscribed: {chat_id}")
        else:
            await update.message.reply_text(
                "ℹ️ 이미 구독이 해제되어 있습니다.\n"
                "구독을 시작하시려면 /start 명령을 사용해주세요."
            )
            logger.info(f"Already unsubscribed user tried to unsubscribe: {chat_id}")


async def check_and_send_news(context: ContextTypes.DEFAULT_TYPE):
    """Check RSS feed and send new articles to subscribers."""
    try:
        # Fetch and parse RSS feed
        feed = feedparser.parse("https://feeds.feedburner.com/geeknews-feed")

        if not feed.entries:
            logger.warning("No entries found in RSS feed")
            return

        subscribers = get_subscribers()
        if not subscribers:
            logger.info("No subscribers to send news to")
            return

        # Process entries (newest first)
        new_articles_count = 0
        for entry in reversed(feed.entries):  # Process all articles
            link = entry.get("link", "")
            article_id = (
                re.search(r"\?id=(\d+)", link).group(1)
                if re.search(r"\?id=(\d+)", link)
                else None
            )

            if not article_id or is_article_sent(article_id):
                continue

            # Format message
            title = entry.get("title", "No title")
            link = entry.get("link", "")

            content = entry.content[0].value if entry.content else ""

            # HTML 태그를 텔레그램 친화적으로 변환
            # <ul> 태그 제거
            content = re.sub(r"<ul>", "", content)
            content = re.sub(r"</ul>", "", content)
            # <li> 태그를 줄바꿈으로 변경
            content = re.sub(r"<li>", "\n• ", content)
            content = re.sub(r"</li>", "", content)
            # CDATA 제거
            content = re.sub(r"<!\[CDATA\[", "", content)
            content = re.sub(r"\]\]>", "", content)
            # 기타 HTML 태그 제거 (strong, p 등)
            content = re.sub(r"<strong>", "<b>", content)
            content = re.sub(r"</strong>", "</b>", content)
            content = re.sub(r"<p>", "", content)
            content = re.sub(r"</p>", "\n", content)
            # 연속된 줄바꿈 정리
            content = re.sub(r"\n{3,}", "\n\n", content)
            content = content.strip()

            message = f"📰 <b>{title}</b>\n\n"
            if content:
                message += f"{content}\n\n"
            message += f"🔗 <a href='{link}&utm_source=telegram&utm_medium=bot'>자세히 보기</a>"

            # Send to all subscribers
            for chat_id in subscribers:
                try:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode="HTML",
                        disable_web_page_preview=False,
                    )
                    await asyncio.sleep(0.5)  # Rate limiting
                except Exception as e:
                    logger.error(f"Error sending to {chat_id}: {e}")
                    # If user blocked the bot, unsubscribe them
                    if "Forbidden" in str(e) or "blocked" in str(e).lower():
                        remove_subscriber(chat_id)
                        logger.info(f"Unsubscribed blocked user: {chat_id}")
                    else:
                        # Retry without content
                        try:
                            simple_message = f"📰 <b>{title}</b>\n\n"
                            simple_message += f"🔗 <a href='{link}&utm_source=telegram&utm_medium=bot'>자세히 보기</a>"
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text=simple_message,
                                parse_mode="HTML",
                                disable_web_page_preview=False,
                            )
                            logger.info(
                                f"Retry successful without content for {chat_id}"
                            )
                        except Exception as retry_error:
                            logger.error(f"Retry failed for {chat_id}: {retry_error}")

            mark_article_sent(article_id)
            new_articles_count += 1
            logger.info(f"Sent article: {title}")

        if new_articles_count > 0:
            logger.info(
                f"Sent {new_articles_count} new articles to {len(subscribers)} subscribers"
            )

    except Exception as e:
        logger.error(f"Error in check_and_send_news: {e}")


def main():
    """Start the bot."""
    # Initialize database
    init_db()

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler(["start", "sub"], start))
    application.add_handler(CommandHandler(["stop", "unsub"], stop))

    # Schedule RSS check (every 5 minutes)
    job_queue = application.job_queue
    job_queue.run_repeating(check_and_send_news, interval=300, first=10)

    logger.info("Bot started successfully")

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
