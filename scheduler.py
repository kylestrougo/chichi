'''
from app import scheduler
from apscheduler.triggers.cron import CronTrigger
from app.routes import tournament_start
from helper import update_data, send_leaderboard_email
from datetime import datetime
from flask_apscheduler import APScheduler

#scheduler = APScheduler()
#scheduler.init_app(app)

def add_jobs():
    scheduler.add_job(id='refresh_scores', func=update_data, trigger='interval', seconds=10)

    start_date = datetime(2023, 12, 15, 17, 44, 0)
    end_date = datetime(2023, 12, 25, 17, 7, 30)

    trigger = CronTrigger(hour=17, minute=23, second=0)
    scheduler.add_job(id='email_leaderboard', func=send_leaderboard_email, trigger=trigger, start_date=start_date,
                      end_date=end_date)

    scheduler.add_job(id='grant_access', func=tournament_start, run_date=start_date)
    scheduler.add_job(id='revoke_access', func=tournament_start, run_date=start_date)


if __name__ == '__main__':
    #scheduler.init_app(app)

    #scheduler.start()
    add_jobs()

'''