from bot import application, send_usage_to_all_telegram_users

def main():
    application.job_queue.run_repeating(send_usage_to_all_telegram_users, interval=3600)

    application.run_polling()

if __name__ == "__main__":
    main()
