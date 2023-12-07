from app import app, scheduler, APScheduler
from helper import update_data, send_leaderboard_email
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime


if __name__ == '__main__':
    # Update Masters data ever 15 seconds
    scheduler.add_job(id='masters_data', func=update_data, trigger='interval', seconds=15)

    # Email leaderboard EOD
    start_date = datetime(2023, 12, 1)
    end_date = datetime(2023, 12, 10)
    trigger = CronTrigger(hour=15, minute=1, second=10)
    scheduler.add_job(id='email_leaderboard', func=send_leaderboard_email, trigger=trigger, start_date=start_date, end_date=end_date)

    # start jobs and app
    scheduler.start()
    app.run(debug=True, host='0.0.0.0')
