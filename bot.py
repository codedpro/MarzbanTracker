from telegram import Bot
from telegram.constants import ParseMode
from decouple import config

TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN")  
bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def send_message(chat_id, message):
    await bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.MARKDOWN)
