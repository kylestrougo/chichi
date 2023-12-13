from apscheduler.triggers.cron import CronTrigger
from flask import Flask
from app.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_moment import Moment
from flask_mail import Mail
from flask_apscheduler import APScheduler

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
moment = Moment(app)
app.config['STATIC_FOLDER'] = 'static'
mail = Mail(app)
scheduler = APScheduler()
##scheduler.init_app(app)


# to  update with prod URL  domain?
##app.config['SESSION_COOKIE_DOMAIN'] = 'localhost.localdomain'

from app import routes, models
from app.routes import tournament_start
from helper import update_data, send_leaderboard_email
from datetime import datetime
import os

def add_jobs():
    scheduler.add_job(id='refresh_scores', func=update_data, trigger='interval', seconds=30)

    start_date = datetime(2023, 12, 13, 13, 41, 0)
    end_date = datetime(2023, 12, 25, 17, 7, 30)

    trigger = CronTrigger(hour=17, minute=23, second=0)
    scheduler.add_job(id='email_leaderboard', func=send_leaderboard_email, trigger=trigger, start_date=start_date,
                      end_date=end_date)

    scheduler.add_job(id='grant_access', func=tournament_start, run_date=start_date)
    scheduler.add_job(id='revoke_access', func=tournament_start, run_date=start_date)


def initialize_scheduler():
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        scheduler.init_app(app)
        add_jobs()
        scheduler.start()