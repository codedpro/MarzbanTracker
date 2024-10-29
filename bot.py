from telegram import (
    Bot,
    Update,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from decouple import config
from telegram.error import TelegramError
from sqlalchemy.orm import Session
from sqlalchemy import text
from db import SessionLocal
import os
import subprocess
from datetime import datetime
from urllib.parse import urlparse, parse_qs

TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_IDS = list(map(int, config("TELEGRAM_USER_IDS").split(",")))
SQLALCHEMY_DATABASE_URL = config("SQLALCHEMY_DATABASE_URL")

application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

async def send_message(chat_id, message):
    await application.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Update Statistics", "Backup Now"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Welcome! Use the keyboard below to interact with the bot.",
        reply_markup=reply_markup,
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Update Statistics":
        await send_usage_to_user(update.message.chat_id)
    elif text == "Backup Now":
        await backup_database_and_send(update.message.chat_id)
    else:
        await update.message.reply_text("Unknown command. Please use the provided buttons.")

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
    message = ""
    for row in admin_data:
        admin_id, username, is_sudo, created_at, telegram_id, discord_webhook, lifetime_used_traffic = row
        message += (
            f"*Admin:* {username}\n"
            f"*Lifetime Used Traffic:* {lifetime_used_traffic / (1024 ** 3):.2f} GB\n\n"
        )
    if message:
        try:
            await send_message(chat_id, message)
        except TelegramError as te:
            print(f"Failed to send message to {chat_id}: {te}")
        except Exception as e:
            print(f"Unexpected error sending message to {chat_id}: {e}")
    else:
        await send_message(chat_id, "No usage data available.")

async def send_usage_to_all_telegram_users(context: ContextTypes.DEFAULT_TYPE):
    for user_id in TELEGRAM_USER_IDS:
        await send_usage_to_user(user_id)

async def backup_database_and_send(chat_id):
    backup_file_path = backup_database()
    if backup_file_path:
        try:
            with open(backup_file_path, 'rb') as f:
                await application.bot.send_document(chat_id=chat_id, document=f)
            os.remove(backup_file_path)
        except Exception as e:
            print(f"Failed to send backup to {chat_id}: {e}")
    else:
        await application.bot.send_message(chat_id=chat_id, text="Backup failed.")

def backup_database():
    url = urlparse(SQLALCHEMY_DATABASE_URL)
    db_user = url.username
    db_password = url.password
    db_host = url.hostname
    db_name = url.path.lstrip('/')

    backup_file_name = f"mysql_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.sql"
    backup_file_path = os.path.join('/tmp', backup_file_name)

    try:
        subprocess.run(
            [
                "mysqldump",
                f"--user={db_user}",
                f"--password={db_password}",
                f"--host={db_host}",
                db_name,
                "--result-file", backup_file_path
            ],
            check=True
        )
        print(f"Database backup created at {backup_file_path}")
        return backup_file_path
    except subprocess.CalledProcessError as e:
        print(f"Database backup failed: {e}")
        return None

async def send_backup_to_all_users(context: ContextTypes.DEFAULT_TYPE):
    for user_id in TELEGRAM_USER_IDS:
        await backup_database_and_send(user_id)

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
