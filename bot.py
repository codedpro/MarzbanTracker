# bot.py

from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from decouple import config
from telegram.error import TelegramError
from sqlalchemy.orm import Session
from sqlalchemy import text
from db import SessionLocal

TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_IDS = list(map(int, config("TELEGRAM_USER_IDS").split(",")))

async def send_message(chat_id, message):
    await application.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Update Statistics", callback_data="update_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome! Click the button below to update statistics.",
        reply_markup=reply_markup,
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "update_stats":
        await send_usage_to_user(query.message.chat_id)

async def fetch_lifetime_used_traffic():
    db = SessionLocal()
    try:
        query = text("CALL GetAdminsWithLifetimeUsage(10, 0);")
        result = db.execute(query)
        admin_data = result.fetchall()
        return admin_data
    except Exception as e:
        print(f"Error fetching data from database: {e}")
        return []
    finally:
        db.close()

async def send_usage_to_user(chat_id):
    admin_data = await fetch_lifetime_used_traffic()
    for row in admin_data:
        admin_id, username, is_sudo, created_at, telegram_id, discord_webhook, lifetime_used_traffic = row
        message = (
            f"*Admin:* {username}\n"
            f"*Lifetime Used Traffic:* {lifetime_used_traffic / (1024 ** 3):.2f} GB\n"
        )
        try:
            await send_message(chat_id, message)
        except TelegramError as te:
            print(f"Failed to send message to {chat_id}: {te}")
        except Exception as e:
            print(f"Unexpected error sending message to {chat_id}: {e}")

async def send_usage_to_all_telegram_users(context: ContextTypes.DEFAULT_TYPE):
    admin_data = await fetch_lifetime_used_traffic()
    for row in admin_data:
        admin_id, username, is_sudo, created_at, telegram_id, discord_webhook, lifetime_used_traffic = row
        message = (
            f"*Admin:* {username}\n"
            f"*Lifetime Used Traffic:* {lifetime_used_traffic / (1024 ** 3):.2f} GB\n"
        )
        for user_id in TELEGRAM_USER_IDS:
            await send_usage_to_user(user_id)

application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_click))
