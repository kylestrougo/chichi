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
# to  update with prod URL  domain?
#app.config['SESSION_COOKIE_DOMAIN'] = 'chi-chi.duckdns.org'
#app.config['REMEMBER_COOKIE_DOMAIN'] = '.chi-chi.duckdns.org'
#app.config['SESSION_COOKIE_SECURE'] = False
#app.config['REMEMBER_COOKIE_SECURE'] = False


scheduler = APScheduler()

from app import routes, models

