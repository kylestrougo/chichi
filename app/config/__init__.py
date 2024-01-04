import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'qwert54321'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ADMINS = ['chi.chi.masters1@gmail.com']
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = 1
    MAIL_USERNAME = 'chi.chi.masters1'
    MAIL_PASSWORD = 'nuyp jlke pbti dceb'

    #mac
    ##SERVER_NAME = '192.168.1.117:5000' # Replace with your server's hostname and port
    #pi
    #SERVER_NAME = '192.168.1.159:5000' # Replace with your server's hostname and port
    #prod
    SERVER_NAME = 'chi-chi.duckdns.org' # Replace with your server's hostname and port
    APPLICATION_ROOT = '/' # Set if your app is hosted under a subpath
    PREFERRED_URL_SCHEME = 'https'