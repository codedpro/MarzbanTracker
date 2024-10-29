from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from decouple import config
from telegram.error import TelegramError

TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def send_message(chat_id, message):
    await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Update Statistics", callback_data="update_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Click the button below to update statistics.", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "update_stats":
        await send_usage_to_user(query.message.chat_id)

async def send_usage_to_user(chat_id):
    from main import fetch_lifetime_used_traffic, SessionLocal

    db = SessionLocal()
    try:
        admin_data = await fetch_lifetime_used_traffic(db)
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
    finally:
        db.close()

application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_click))
