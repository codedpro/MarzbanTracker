from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db import SessionLocal
from bot import send_message
from sqlalchemy import text

app = FastAPI()

TELEGRAM_USER_IDS = [373342220] 

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def fetch_lifetime_used_traffic(db: Session):
    query = text("CALL GetAdminsWithLifetimeUsage(10, 0);")
    result = db.execute(query)
    admin_data = result.fetchall()
    return admin_data

async def send_usage_to_telegram():
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
                await send_message(user_id, message)
    finally:
        db.close()

scheduler = AsyncIOScheduler()
scheduler.add_job(send_usage_to_telegram, "interval", hours=1)
scheduler.start()

@app.on_event("startup")
async def startup_event():
    await send_usage_to_telegram()

@app.get("/")
async def root():
    return {"message": "Telegram Bot with FastAPI to send admin usage"}

