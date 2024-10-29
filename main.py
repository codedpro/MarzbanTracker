from bot import application, send_usage_to_all_telegram_users, send_backup_to_all_users

def main():
    application.job_queue.run_repeating(send_usage_to_all_telegram_users, interval=3600)

    application.job_queue.run_repeating(send_backup_to_all_users, interval=3600)

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
