from app import app, initialize_scheduler,scheduler
from helper import update_data, send_leaderboard_email
from app.routes import tournament_start
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
'''
# ----------------- Tournament Dates -----------------
start_date = datetime(2023, 12, 13, 13, 41, 0)
end_date = datetime(2023, 12, 25, 17, 7, 30)

# ----------------- Masters data every 30 seconds -----------------
scheduler.add_job(id='refresh_scores', func=update_data, trigger='interval', seconds=10)

# ----------------- Leaderboard Report every EOD -----------------
trigger = CronTrigger(hour=17, minute=23, second=0)
scheduler.add_job(id='email_leaderboard', func=send_leaderboard_email, trigger=trigger, start_date=start_date,
                  end_date=end_date)

# ----------------- Upon tournament start, give access to other user profiles -----------------
scheduler.add_job(id='grant_access', func=tournament_start, run_date=start_date)

# ----------------- Revoke Drafting Capabilities at -----------------
scheduler.add_job(id='revoke_access', func=tournament_start, run_date=start_date)

'''

if __name__ == '__main__':
    # ----------------- Start Jobs, Start App -----------------
    ##scheduler.start()
    initialize_scheduler()

    app.run(debug=True, host='0.0.0.0')
