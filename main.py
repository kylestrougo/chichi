from app import app, scheduler
from helper import update_data, send_leaderboard_email
from app.routes import grant_access_to_other_user_data, revoke_access_to_drafting
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime


if __name__ == '__main__':
    access_trigger = 0
    # ----------------- Masters data every 30 seconds -----------------
    scheduler.add_job(id='masters_data', func=update_data, trigger='interval', seconds=30)

    # ----------------- Leaderboard Report every EOD -----------------
    start_date = datetime(2023, 12, 1)
    end_date = datetime(2024, 1, 1)
    trigger = CronTrigger(hour=15, minute=1, second=10)
    scheduler.add_job(id='email_leaderboard', func=send_leaderboard_email, trigger=trigger, start_date=start_date,end_date=end_date)

    # ----------------- Grant Access to other User's Data at -----------------
    access_date = datetime(2023, 12, 8, 18, 18, 20)
    scheduler.add_job(id='grant_access_to_other_user_data', func=grant_access_to_other_user_data, run_date=access_date)

    # ----------------- Revoke Drafting Capabilities at -----------------
    revoke_access_date = datetime(2024, 1, 1, 8, 0, 0)
    #scheduler.add_job(revoke_access_to_drafting, 'date', run_date=revoke_access_date)

    # ----------------- Start Jobs, Start App -----------------
    scheduler.start()

    app.run(debug=True, host='0.0.0.0')
