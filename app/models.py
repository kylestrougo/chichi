from app import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    draft = db.relationship('Draft', backref='user', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        ##return '<User {}>'.format(self.username)
        return f"{self.username}"


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)


class Masters(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pos = db.Column(db.String(4))
    player = db.Column(db.String(255))
    r1 = db.Column(db.String(4))
    r2 = db.Column(db.String(4))
    r3 = db.Column(db.String(4))
    r4 = db.Column(db.String(4))
    to_par = db.Column(db.String(4))

    def __repr__(self):
        return f"<tr><td>{self.pos}</td><td>{self.player}</td><td>{self.r1}</td><td>{self.r2}</td><td>{self.r3}</td><td>{self.r4}</td><td>{self.to_par}</td>"


class updated(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.String(255))

    def __repr__(self):
        return self.datetime


class Draft(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tier1 = db.Column(db.String(64))
    tier2 = db.Column(db.String(64))
    tier3 = db.Column(db.String(64))
    tier4 = db.Column(db.String(64))
    tier5 = db.Column(db.String(64))
    tier6 = db.Column(db.String(64))

    def __repr__(self):
        return f"User: {self.user_id}, Tier1: {self.tier1}, Tier2: {self.tier2}, Tier3: {self.tier3}, Tier4: {self.tier4}, Tier5: {self.tier5}, Tier6: {self.tier6}"