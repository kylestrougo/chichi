from app import app, db, scheduler
from app.models import TournamentStatus
from helper import update_data, send_leaderboard_email
from app.routes import tournament_start
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import os


def add_jobs():
    # tournament dates
    t_start = datetime(2024, 3, 24, 9, 0, 0)
    t_end = datetime(2024, 3, 27, 22, 0, 0)

    #day1 dates
    end_dt_d1 = datetime(2024, 2, 8, 22, 0, 0)
    scheduler.add_job(id='refresh_scores1', func=update_data, trigger='interval', minutes=30, start_date=t_start, end_date=end_dt_d1)

    #day2 dates
    start_dt_d2 = datetime(2024, 2, 9, 9, 0, 0)
    end_dt_d2 = datetime(2024, 2, 9, 22, 0, 0)
    scheduler.add_job(id='refresh_scores2', func=update_data, trigger='interval', minutes=10, start_date=start_dt_d2, end_date=end_dt_d2)

    #day3 dates
    start_dt_d3 = datetime(2024, 2, 10, 9, 0, 0)
    end_dt_d3 = datetime(2024, 2, 10, 22, 0, 0)
    scheduler.add_job(id='refresh_scores3', func=update_data, trigger='interval', minutes=5, start_date=start_dt_d3, end_date=end_dt_d3)

    #day4 dates
    start_dt_d4 = datetime(2024, 2, 11, 9, 0, 0)
    end_dt_d4 = datetime(2024, 2, 11, 22, 0, 0)
    scheduler.add_job(id='refresh_scores4', func=update_data, trigger='interval', minutes=2, start_date=start_dt_d4, end_date=end_dt_d4)

    email_trigger = CronTrigger(hour=20, minute=0, second=0)
    scheduler.add_job(id='email_leaderboard', func=send_leaderboard_email, trigger=email_trigger, start_date=t_start,
                      end_date=t_end)

    scheduler.add_job(id='grant_revoke_access', func=tournament_start, run_date=t_start)


def initialize_scheduler():
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        scheduler.init_app(app)
        add_jobs()
        scheduler.start()

if __name__ == '__main__':
    # reset the status of TournamentStatus
    ##app.app_context().push()
    with app.app_context():

        db.session.query(TournamentStatus).delete()
        s = TournamentStatus(status=0)
        db.session.add(s)
        db.session.commit()
        print("TournamentStatus: ", TournamentStatus.query.first())

        initialize_scheduler()
        app.run(debug=True, host='0.0.0.0')
        ##os.system("gunicorn -w 1 -b 0.0.0.0:5000 app:app")

