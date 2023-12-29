from app import app, db, scheduler
from app.models import TournamentStatus
from helper import update_data, send_leaderboard_email
from app.routes import tournament_start
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import os


def add_jobs():
    ##scheduler.add_job(id='refresh_scores', func=update_data, trigger='interval', seconds=30)

    start_date = datetime(2023, 12, 29, 16, 31, 0)
    end_date = datetime(2024, 12, 30, 17, 7, 30)

    email_trigger = CronTrigger(hour=16, minute=31, second=0)
    scheduler.add_job(id='email_leaderboard', func=send_leaderboard_email, trigger=email_trigger, start_date=start_date,
                      end_date=end_date)

    scheduler.add_job(id='grant_revoke_access', func=tournament_start, run_date=start_date)


def initialize_scheduler():
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        scheduler.init_app(app)
        add_jobs()
        scheduler.start()

if __name__ == '__main__':
    # reset the status of TournamentStatus
    app.app_context().push()
    db.session.query(TournamentStatus).delete()
    s = TournamentStatus(status=0)
    db.session.add(s)
    db.session.commit()
    print("TournamentStatus: ", TournamentStatus.query.first())

    initialize_scheduler()
    app.run(debug=True, host='0.0.0.0')

