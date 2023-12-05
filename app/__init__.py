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
scheduler.init_app(app)

from app import routes, models

