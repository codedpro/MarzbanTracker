from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
from db import SessionLocal
from bot import send_usage_to_user, application
from sqlalchemy import text
from decouple import config
import asyncio

TELEGRAM_USER_IDS = list(map(int, config("TELEGRAM_USER_IDS").split(",")))

async def fetch_lifetime_used_traffic(db: Session):
    try:
        query = text("CALL GetAdminsWithLifetimeUsage(10, 0);")
        result = db.execute(query)
        admin_data = result.fetchall()
        return admin_data
    except Exception as e:
        print(f"Error fetching data from database: {e}")
        return []

async def send_usage_to_all_telegram_users():
    db = SessionLocal()
    try:
        admin_data = await fetch_lifetime_used_traffic(db)
        for row in admin_data:
            admin_id, username, is_sudo, created_at, telegram_id, discord_webhook, lifetime_used_traffic = row
            message = (
                f"*Admin:* {username}\n"
                f"*Lifetime Used Traffic:* {lifetime_used_traffic / (1024 ** 3):.2f} GB\n"
            )
            for user_id in TELEGRAM_USER_IDS:
                try:
                    await send_usage_to_user(user_id, message)
                except Exception as e:
                    print(f"Failed to send message to {user_id}: {e}")
    finally:
        db.close()

scheduler = AsyncIOScheduler()
scheduler.add_job(send_usage_to_all_telegram_users, "interval", hours=1)
scheduler.start()

async def main():
    await application.initialize()
    await application.start()
    await application.idle()

if __name__ == "__main__":
    asyncio.run(main())
